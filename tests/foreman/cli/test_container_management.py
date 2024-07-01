"""Tests for the Container Management Content

:Requirement: ContainerManagement-Content

:CaseAutomation: Automated

:Team: Phoenix-content

:CaseComponent: ContainerManagement-Content

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    REPO_TYPE,
)
from robottelo.logging import logger


def _repo(sat, product_id, name=None, upstream_name=None, url=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to CONTAINER_UPSTREAM_NAME constant.
    :param str url: URL of repository. If ``None`` then defaults to
        CONTAINER_REGISTRY_HUB constant.
    :return: A ``Repository`` object.
    """
    return sat.cli_factory.make_repository(
        {
            'content-type': REPO_TYPE['docker'],
            'docker-upstream-name': upstream_name or CONTAINER_UPSTREAM_NAME,
            'name': name or gen_string('alpha', 5),
            'product-id': product_id,
            'url': url or CONTAINER_REGISTRY_HUB,
        }
    )


class TestDockerClient:
    """Tests specific to using ``Docker`` as a client to pull Docker images
    from a Satellite 6 instance.

    :CaseImportance: Medium
    """

    @pytest.mark.tier3
    def test_positive_pull_image(self, module_org, container_contenthost, target_sat):
        """A Docker-enabled client can use ``docker pull`` to pull a
        Docker image off a Satellite 6 instance.

        :id: 023f0538-2aad-4f87-b8a8-6ccced648366

        :steps:

            1. Publish and promote content view with Docker content
            2. Register Docker-enabled client against Satellite 6.

        :expectedresults: Client can pull Docker images from server and run it.

        :parametrized: yes
        """
        product = target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
        repo = _repo(target_sat, product['id'])
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        try:
            result = container_contenthost.execute(
                f'docker login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {target_sat.hostname}'
            )
            assert result.status == 0

            # publishing takes few seconds sometimes
            result, _ = wait_for(
                lambda: container_contenthost.execute(f'docker pull {repo["published-at"]}'),
                num_sec=60,
                delay=2,
                fail_condition=lambda out: out.status != 0,
                logger=logger,
            )
            assert result.status == 0
            try:
                result = container_contenthost.execute(f'docker run {repo["published-at"]}')
                assert result.status == 0
            finally:
                # Stop and remove the container
                result = container_contenthost.execute(
                    f'docker ps -a | grep {repo["published-at"]}'
                )
                container_id = result.stdout[0].split()[0]
                container_contenthost.execute(f'docker stop {container_id}')
                container_contenthost.execute(f'docker rm {container_id}')
        finally:
            # Remove docker image
            container_contenthost.execute(f'docker rmi {repo["published-at"]}')

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier3
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_search(
        self, module_org, container_contenthost, target_sat
    ):
        """Verify that docker command line can be used against
        Satellite server to search for container images stored
        on Satellite instance.

        :id: cefa74e1-e40d-4f47-853b-1268643cea2f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set 'Unauthenticated Pull' option to false
            3. Try to search for docker images on Satellite
            4. Use Docker client to login to Satellite docker hub
            5. Search for docker images
            6. Use Docker client to log out of Satellite docker hub
            7. Try to search for docker images (ensure last search result
               is caused by change of Satellite option and not login/logout)
            8. Set 'Unauthenticated Pull' option to true
            9. Search for docker images

        :expectedresults: Client can search for docker images stored
            on Satellite instance

        :parametrized: yes
        """
        pattern_prefix = gen_string('alpha', 5)
        registry_name_pattern = (
            f'{pattern_prefix}-<%= content_view.label %>/<%= repository.docker_upstream_name %>'
        )

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        lce = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
        product = target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
        repo = _repo(target_sat, product['id'], upstream_name=CONTAINER_UPSTREAM_NAME)
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        content_view = target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': repo['id']}
        )
        target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = target_sat.cli.ContentView.info({'id': content_view['id']})
        target_sat.cli.ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-name-pattern': registry_name_pattern,
                'registry-unauthenticated-pull': 'false',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        docker_repo_uri = (
            f' {target_sat.hostname}/{pattern_prefix}-{content_view["label"]}/'
            f'{CONTAINER_UPSTREAM_NAME} '
        ).lower()

        # 3. Try to search for docker images on Satellite
        remote_search_command = f'docker search {target_sat.hostname}/{CONTAINER_UPSTREAM_NAME}'
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri not in result.stdout

        # 4. Use Docker client to login to Satellite docker hub
        result = container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0

        # 5. Search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

        # 6. Use Docker client to log out of Satellite docker hub
        result = container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri not in result.stdout

        # 8. Set 'Unauthenticated Pull' option to true
        target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-unauthenticated-pull': 'true',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )

        # 9. Search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier3
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_pull(
        self, module_org, container_contenthost, target_sat
    ):
        """Verify that docker command line can be used against
        Satellite server to pull in container images stored
        on Satellite instance.

        :id: 2a331f88-406b-4a5c-ae70-302a9994077f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set 'Unauthenticated Pull' option to false
            3. Try to pull in docker image from Satellite
            4. Use Docker client to login to Satellite container registry
            5. Pull in docker image
            6. Use Docker client to log out of Satellite container registry
            7. Try to pull in docker image (ensure next pull result
               is caused by change of Satellite option and not login/logout)
            8. Set 'Unauthenticated Pull' option to true
            9. Pull in docker image

        :expectedresults: Client can pull in docker images stored
            on Satellite instance

        :parametrized: yes
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = CONTAINER_UPSTREAM_NAME
        registry_name_pattern = (
            f'{pattern_prefix}-<%= content_view.label %>/<%= repository.docker_upstream_name %>'
        )

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        lce = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
        product = target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
        repo = _repo(target_sat, product['id'], upstream_name=docker_upstream_name)
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        content_view = target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': repo['id']}
        )
        target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = target_sat.cli.ContentView.info({'id': content_view['id']})
        target_sat.cli.ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-name-pattern': registry_name_pattern,
                'registry-unauthenticated-pull': 'false',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        docker_repo_uri = (
            f'{target_sat.hostname}/{pattern_prefix}-{content_view["label"]}/'
            f'{docker_upstream_name}'
        ).lower()

        # 3. Try to pull in docker image from Satellite
        docker_pull_command = f'docker pull {docker_repo_uri}'
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 1

        # 4. Use Docker client to login to Satellite docker hub
        result = container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0

        # 5. Pull in docker image
        # publishing takes few seconds sometimes
        result, _ = wait_for(
            lambda: container_contenthost.execute(docker_pull_command),
            num_sec=60,
            delay=2,
            fail_condition=lambda out: out.status != 0,
            logger=logger,
        )
        assert result.status == 0

        # 6. Use Docker client to log out of Satellite docker hub
        result = container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to pull in docker image
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 1

        # 8. Set 'Unauthenticated Pull' option to true
        target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-unauthenticated-pull': 'true',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )

        # 9. Pull in docker image
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 0

    def test_negative_pull_content_with_longer_name(
        self, target_sat, container_contenthost, module_org
    ):
        """Verify that long name CV publishes when CV & docker repo both have a larger name.

        :id: e0ac0be4-f5ff-4a88-bb29-33aa2d874f46

        :steps:

            1. Create Product, docker repo, CV and LCE with a long name
            2. Sync the repos
            3. Add repository to CV, Publish, and then Promote CV to LCE
            4. Pull in docker image

        :expectedresults:

            1. Long Product, repository, CV and LCE should create successfully
            2. Sync repository successfully
            3. Publish & Promote should success
            4. Can pull in docker images

        :BZ: 2127470

        :customerscenario: true
        """
        pattern_postfix = gen_string('alpha', 10).lower()

        product_name = f'containers-{pattern_postfix}'
        repo_name = f'repo-{pattern_postfix}'
        lce_name = f'lce-{pattern_postfix}'
        cv_name = f'cv-{pattern_postfix}'

        # 1. Create Product, docker repo, CV and LCE with a long name
        product = target_sat.cli_factory.make_product_wait(
            {'name': product_name, 'organization-id': module_org.id}
        )

        repo = _repo(
            target_sat, product['id'], name=repo_name, upstream_name=CONTAINER_UPSTREAM_NAME
        )

        # 2. Sync the repos
        target_sat.cli.Repository.synchronize({'id': repo['id']})

        lce = target_sat.cli_factory.make_lifecycle_environment(
            {'name': lce_name, 'organization-id': module_org.id}
        )
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'composite': False, 'organization-id': module_org.id}
        )

        # 3. Add repository to CV, Publish, and then Promote CV to LCE
        target_sat.cli.ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})

        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        target_sat.cli.ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )

        podman_pull_command = (
            f"podman pull --tls-verify=false {target_sat.hostname}/{module_org.label.lower()}"
            f"-{lce['label'].lower()}-{cv['label'].lower()}-{product['label'].lower()}-{repo_name}"
        )

        # 4. Pull in docker image
        assert (
            container_contenthost.execute(
                f'podman login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {target_sat.hostname}'
            ).status
            == 0
        )

        assert container_contenthost.execute(podman_pull_command).status == 0

        assert container_contenthost.execute(f'podman logout {target_sat.hostname}').status == 0
