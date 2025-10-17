"""Tests for the Container Management Content

:Requirement: ContainerImageManagement

:CaseAutomation: Automated

:Team: Artemis

:CaseComponent: ContainerImageManagement

"""

from datetime import UTC, datetime

from box import Box
from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FOREMAN_CONFIG_SETTINGS_YAML, REPO_TYPE
from robottelo.logging import logger


def _repo(sat, product_id, name=None, upstream_name=None, url=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to settings.container.upstream_name constant.
    :param str url: URL of repository. If ``None`` then defaults to
        settings.container.registry_hub constant.
    :return: A ``Repository`` object.
    """
    return sat.cli_factory.make_repository(
        {
            'content-type': REPO_TYPE['docker'],
            'docker-upstream-name': upstream_name or settings.container.upstream_name,
            'name': name or gen_string('alpha', 5),
            'product-id': product_id,
            'url': url or settings.container.registry_hub,
        }
    )


class TestDockerClient:
    """Tests specific to using ``Docker`` as a client to pull Docker images
    from a Satellite 6 instance.

    :CaseImportance: Medium
    """

    def test_positive_pull_image(
        self, request, module_org, module_container_contenthost, target_sat
    ):
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
            result = module_container_contenthost.execute(
                f'docker login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {target_sat.hostname}'
            )
            assert result.status == 0
            request.addfinalizer(
                lambda: module_container_contenthost.execute(f'docker logout {target_sat.hostname}')
            )

            # publishing takes few seconds sometimes
            result, _ = wait_for(
                lambda: module_container_contenthost.execute(f'docker pull {repo["published-at"]}'),
                num_sec=60,
                delay=2,
                fail_condition=lambda out: out.status != 0,
                logger=logger,
            )
            assert result.status == 0
            try:
                result = module_container_contenthost.execute(f'docker run {repo["published-at"]}')
                assert result.status == 0
            finally:
                # Stop and remove the container
                result = module_container_contenthost.execute(
                    f'docker ps -a | grep {repo["published-at"]}'
                )
                container_id = result.stdout[0].split()[0]
                module_container_contenthost.execute(f'docker stop {container_id}')
                module_container_contenthost.execute(f'docker rm {container_id}')
        finally:
            # Remove docker image
            module_container_contenthost.execute(f'docker rmi {repo["published-at"]}')

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_search(
        self, request, module_org, module_container_contenthost, target_sat
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
        repo = _repo(target_sat, product['id'], upstream_name=settings.container.upstream_name)
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
            f'{settings.container.upstream_name}'
        ).lower()

        # 3. Try to search for docker images on Satellite
        remote_search_command = (
            f'docker search {target_sat.hostname}/{settings.container.upstream_name}'
        )
        result = module_container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri not in result.stdout

        # 4. Use Docker client to login to Satellite docker hub
        result = module_container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0
        request.addfinalizer(
            lambda: module_container_contenthost.execute(f'docker logout {target_sat.hostname}')
        )

        # 5. Search for docker images
        result = module_container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

        # 6. Use Docker client to log out of Satellite docker hub
        result = module_container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to search for docker images
        result = module_container_contenthost.execute(remote_search_command)
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
        result = module_container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_pull(
        self, request, module_org, module_container_contenthost, target_sat
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
        docker_upstream_name = settings.container.upstream_name
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
            f'{target_sat.hostname}/{pattern_prefix}-{content_view["label"]}/{docker_upstream_name}'
        ).lower()

        # 3. Try to pull in docker image from Satellite
        docker_pull_command = f'docker pull {docker_repo_uri}'
        result = module_container_contenthost.execute(docker_pull_command)
        assert result.status != 0

        # 4. Use Docker client to login to Satellite docker hub
        result = module_container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0
        request.addfinalizer(
            lambda: module_container_contenthost.execute(f'docker logout {target_sat.hostname}')
        )

        # 5. Pull in docker image
        # publishing takes few seconds sometimes
        result, _ = wait_for(
            lambda: module_container_contenthost.execute(docker_pull_command),
            num_sec=60,
            delay=2,
            fail_condition=lambda out: out.status != 0,
            logger=logger,
        )
        assert result.status == 0

        # 6. Use Docker client to log out of Satellite docker hub
        result = module_container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to pull in docker image
        result = module_container_contenthost.execute(docker_pull_command)
        assert result.status != 0

        # 8. Set 'Unauthenticated Pull' option to true
        target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-unauthenticated-pull': 'true',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )

        # 9. Pull in docker image
        result = module_container_contenthost.execute(docker_pull_command)
        assert result.status == 0

    def test_positive_pull_content_with_longer_name(
        self, request, target_sat, module_container_contenthost, module_org
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
            target_sat,
            product['id'],
            name=repo_name,
            upstream_name=settings.container.upstream_name,
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
            f"podman pull --tls-verify=false {target_sat.hostname}/{module_org.label}"
            f"/{lce['label']}/{cv['label']}/{product['label']}/{repo_name}".lower()
        )

        # 4. Pull in docker image
        assert (
            module_container_contenthost.execute(
                f'podman login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {target_sat.hostname}'
            ).status
            == 0
        )
        request.addfinalizer(
            lambda: module_container_contenthost.execute(f'podman logout {target_sat.hostname}')
        )

        assert module_container_contenthost.execute(podman_pull_command).status == 0

    @pytest.fixture(scope='module')
    def stage_setup(
        self, module_target_sat, module_capsule_configured, module_org, module_lce, module_product
    ):
        """Setup for test_podman_cert_auth"""
        sat, caps = module_target_sat, module_capsule_configured

        # 1. Associate the organization and LCE to the capsule.
        res = sat.cli.Capsule.update({'name': caps.hostname, 'organization-ids': module_org.id})
        assert 'proxy updated' in str(res)

        caps.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': module_lce.id}
        )
        res = caps.nailgun_capsule.content_lifecycle_environments()
        assert len(res['results']) >= 1
        assert module_lce.id in [capsule_lce['id'] for capsule_lce in res['results']]

        # 2. Create and sync a docker repo.
        repo = _repo(sat, module_product.id, upstream_name='quay/busybox', url='https://quay.io')
        sat.cli.Repository.synchronize({'id': repo['id']})

        # 3. Create a CV with the repo, publish and promote it to a LCE, wait for capsule sync.
        cv = sat.cli_factory.make_content_view(
            {'organization-id': module_org.id, 'repository-ids': [repo['id']]}
        )
        timestamp = datetime.now(UTC)
        sat.cli.ContentView.publish({'id': cv['id']})
        cv = sat.cli.ContentView.info({'id': cv['id']})
        sat.cli.ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': module_lce.id}
        )
        module_capsule_configured.wait_for_sync(start_time=timestamp)

        # 4. Create activation key for the LCE/CV.
        ak = sat.cli.ActivationKey.create(
            {
                'name': gen_string('alpha'),
                'organization-id': module_org.id,
                'lifecycle-environment-id': module_lce.id,
                'content-view-id': cv['id'],
            }
        )
        return Box(repo=repo, cv=cv, ak=ak)

    @pytest.mark.e2e
    @pytest.mark.parametrize('target_server', ['sat', 'caps'], ids=['satellite', 'capsule'])
    @pytest.mark.parametrize('gr_certs_setup', [False, True], ids=['manual-setup', 'GR-setup'])
    def test_podman_cert_auth(
        self,
        request,
        module_target_sat,
        module_capsule_configured,
        module_container_contenthost,
        stage_setup,
        target_server,
        gr_certs_setup,
        module_org,
        module_lce,
        module_product,
    ):
        """Verify the podman search and pull works with cert-based authentication for both,
        Satellite and Capsule, without need for login.

        :id: 7b1a457c-ae67-4a76-9f67-9074ea7f858a

        :parametrized: yes

        :Verifies: SAT-33254, SAT-33255, SAT-33260

        :setup:
            1. Associate the organization and LCE to the capsule.
            2. Create and sync a docker repo.
            3. Create a CV with the repo, publish and promote it to a LCE, wait for capsule sync.
            4. Create activation key for the LCE/CV.

        :steps:
            1. Register a host to the LCE/CV environment.
            2. Configure podman certs for authentication (manual setup only).
            3. Try podman search all, ensure Library and repo images are not listed.
            4. Try podman search/pull for Library images, ensure it fails.
            5. Try podman search/pull for the LCE/CV, ensure it works.

        :expectedresults:
            1. Podman search/pull is restricted for Library (or any LCE missing in AK).
            2. Podman search/pull works for environments included in AK.
            3. The above applies for both, Satellite and Capsule.

        """
        server = module_capsule_configured if target_server == 'caps' else module_target_sat
        host = module_container_contenthost
        org, lce, prod = module_org, module_lce, module_product
        repo, cv, ak = stage_setup.repo, stage_setup.cv, stage_setup.ak

        # 1. Register a host to the LCE/CV environment.
        res = host.register(
            org, None, ak.name, server, force=True, setup_container_certs=gr_certs_setup
        )
        assert res.status == 0
        assert host.subscribed

        @request.addfinalizer
        def _finalize():
            host.unregister()
            host.delete_host_record()
            host.reset_podman_cert_auth(server)  # reset regardless how it was set

        # 2. Configure podman certs for authentication (manual setup only).
        if not gr_certs_setup:
            host.configure_podman_cert_auth(server)

        # 3. Try podman search all, ensure Library and repo images are not listed.
        org_prefix = f'{server.hostname}/{org.label}'
        lib_path = f'{org_prefix}/library'.lower()
        repo_path = f'{org_prefix}/{prod.label}/{repo.label}'.lower()
        cv_path = f'{org_prefix}/{lce.label}/{cv.label}/{prod.label}/{repo.label}'.lower()

        finds = host.execute(f'podman search {server.hostname}/').stdout
        assert lib_path not in finds
        assert repo_path not in finds
        assert cv_path in finds
        paths = [f.strip() for f in finds.split('\n') if 'NAME' not in f and len(f)]
        assert len(paths) == 1

        # 4. Try podman search/pull for Library images, ensure it fails.
        for path in [lib_path, repo_path]:
            assert host.execute(f'podman search {path}').stdout == ''
            assert host.execute(f'podman pull {path}').status

        # 5. Try podman search/pull for the LCE/CV, ensure it works.
        res = host.execute(f'podman search {cv_path}')
        assert cv_path in res.stdout
        res = host.execute(f'podman pull {cv_path}')
        assert res.status == 0
        request.addfinalizer(lambda: host.execute(f'podman rmi {cv_path}'))
        res = host.execute('podman images')
        assert cv_path in res.stdout

    def test_destructive_container_registry_with_dns_alias(self, request, target_sat):
        """Test container registry operations with DNS alias

        :id: 10cf21a2-db65-4c02-b3b5-4a5280b4d181

        :steps:
            1. Register Satellite with CDN
            2. Add a DNS alias to the environment by modifying /etc/hosts
            3. Configure foreman's settings.yaml to allow the DNS alias
            4. Pull image from quay.io and use the image id during push
            5. Run podman login with the alias hostname
            6. Run podman push with the alias hostname
            7. Run podman pull with the alias hostname

        :expectedresults:
            1. Container registry operations work with DNS alias
            2. No UnsafeRedirectError occurs during blob operations
            3. Podman pull/push operations succeed with alias hostname

        :Verifies: SAT-36036

        :CaseImportance: High

        :customerscenario: true
        """
        # Generate test data
        alias_hostname = f"alias-{gen_string('alpha', 5).lower()}.example.com"
        org_name = gen_string('alpha', 5).lower()
        product_name = gen_string('alpha', 5).lower()
        repo_name = gen_string('alpha', 5).lower()

        # Create organization and product
        organization = target_sat.api.Organization(name=org_name).create()
        product = target_sat.api.Product(name=product_name, organization=organization).create()

        # Get organization and product labels for container URI
        org_label = organization.label
        product_label = product.label

        # @request.addfinalizer
        def cleanup_org_and_product():
            # Cleanup organization (this will also cleanup the product)
            target_sat.api.Organization(id=organization.id).delete()

        # Step 1: Register Satellite with CDN (already done in setup)

        # Step 2: Add DNS alias to /etc/hosts
        original_hosts = target_sat.execute('cat /etc/hosts').stdout
        hosts_entry = f"{target_sat.ip_addr} {alias_hostname}"

        def add_hosts_entry():
            result = target_sat.execute(f'echo "{hosts_entry}" >> /etc/hosts')
            return result.status == 0

        assert add_hosts_entry()

        @request.addfinalizer
        def restore_hosts():
            # Restore original /etc/hosts
            target_sat.execute(f'echo "{original_hosts}" > /etc/hosts')

        # Step 3: Configure foreman's settings.yaml to allow the DNS alias
        settings_yaml_path = FOREMAN_CONFIG_SETTINGS_YAML
        original_settings = target_sat.execute(f'cat {settings_yaml_path}').stdout

        # Add host configuration to settings.yaml
        host_config = f":hosts:\n  - {alias_hostname}"

        def update_settings():
            result = target_sat.execute(f'echo "{host_config}" >> {settings_yaml_path}')
            return result.status == 0

        assert update_settings()

        # Restart foreman service to apply settings
        target_sat.execute('foreman-maintain service restart')

        @request.addfinalizer
        def restore_settings():
            # Restore original settings.yaml
            target_sat.execute(f'echo "{original_settings}" > {settings_yaml_path}')
            target_sat.execute('systemctl restart foreman')

        # Step 4: Pull image from quay.io
        busybox_image = 'quay.io/quay/busybox'
        pull_result = target_sat.execute(f'podman pull {busybox_image}')
        assert pull_result.status == 0

        # Get the image ID of the pulled busybox image
        images_result = target_sat.execute('podman images --format "{{.ID}} {{.Repository}}"')
        assert images_result.status == 0
        busybox_image_id = None
        for line in images_result.stdout.strip().split('\n'):
            if busybox_image in line:
                busybox_image_id = line.split()[0]
                break
        assert busybox_image_id, f"Could not find image ID for {busybox_image}"

        @request.addfinalizer
        def cleanup_image():
            target_sat.execute(f'podman rmi {busybox_image}')

        # Step 5: Run podman login with the alias hostname
        login_result = target_sat.execute(
            f'podman login {alias_hostname} --tls-verify=false '
            f'-u {settings.server.admin_username} -p {settings.server.admin_password}'
        )
        assert login_result.status == 0

        @request.addfinalizer
        def logout():
            target_sat.execute(f'podman logout {alias_hostname}')

        # Step 6: Run podman push with the alias hostname using image ID
        container_uri = f"{alias_hostname}/{org_label}/{product_label}/{repo_name}"
        push_result = target_sat.execute(
            f'podman push {busybox_image_id} {container_uri} --tls-verify=false'
        )
        assert push_result.status == 0

        # Step 7: Run podman pull with the alias hostname
        pull_result = target_sat.execute(f'podman pull {container_uri} --tls-verify=false')
        assert pull_result.status == 0

        # Verify the image is available
        images_result = target_sat.execute('podman images')
        assert container_uri in images_result.stdout

        # Cleanup pulled image
        @request.addfinalizer
        def cleanup_pulled_image():
            target_sat.execute(f'podman rmi {container_uri}')

        logger.info(
            f"Successfully verified container registry operations with DNS alias {alias_hostname}"
        )
