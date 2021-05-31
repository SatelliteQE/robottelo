"""Test for Repository related Upgrade Scenarios

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Repositories

:Assignee: tpapaioa

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os

from fabric.api import execute
from fabric.api import run
from nailgun import entities
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import dockerize
from upgrade_tests.helpers.scenarios import get_entity_data
from upgrade_tests.helpers.scenarios import rpm1
from upgrade_tests.helpers.scenarios import rpm2

from robottelo import ssh
from robottelo.api.utils import create_sync_custom_repo
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.logging import logger
from robottelo.upgrade_utility import create_repo
from robottelo.upgrade_utility import host_location_update
from robottelo.upgrade_utility import install_or_update_package
from robottelo.upgrade_utility import publish_content_view


UPSTREAM_USERNAME = 'rTtest123'
DOCKER_VM = settings.upgrade.docker_vm
FILE_PATH = '/var/www/html/pub/custom_repo/'
CUSTOM_REPO = f'https://{settings.server.hostname}/pub/custom_repo'
_, RPM1_NAME = os.path.split(rpm1)
_, RPM2_NAME = os.path.split(rpm2)


class TestScenarioRepositoryUpstreamAuthorizationCheck:
    """This test scenario is to verify the upstream username in post-upgrade for a custom
    repository which does have a upstream username but not password set on it in pre-upgrade.

    Test Steps:

        1. Before Satellite upgrade, Create a custom repository and sync it.
        2. Set the upstream username on same repository using foreman-rake.
        3. Upgrade Satellite.
        4. Check if the upstream username value is removed for same repository.
    """

    @pre_upgrade
    def test_pre_repository_scenario_upstream_authorization(self):
        """Create a custom repository and set the upstream username on it.

        :id: preupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Create a custom repository and sync it.
            2. Set the upstream username on same repository using foreman-rake.

        :expectedresults:
            1. Upstream username should be set on repository.

        :BZ: 1641785
        """

        org = entities.Organization().create()
        custom_repo = create_sync_custom_repo(org_id=org.id)
        rake_repo = f'repo = Katello::Repository.find_by_id({custom_repo})'
        rake_username = f'; repo.root.upstream_username = "{UPSTREAM_USERNAME}"'
        rake_repo_save = '; repo.save!(validate: false)'
        result = run(f"echo '{rake_repo}{rake_username}{rake_repo_save}'|foreman-rake console")
        assert 'true' in result

        global_dict = {self.__class__.__name__: {'repo_id': custom_repo}}
        create_dict(global_dict)

    @post_upgrade(depend_on=test_pre_repository_scenario_upstream_authorization)
    def test_post_repository_scenario_upstream_authorization(self):
        """Verify upstream username for pre-upgrade created repository.

        :id: postupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Verify upstream username for pre-upgrade created repository using
            foreman-rake.

        :expectedresults:
            1. upstream username should not exists on same repository.

        :BZ: 1641785
        """

        repo_id = get_entity_data(self.__class__.__name__)['repo_id']
        rake_repo = f'repo = Katello::RootRepository.find_by_id({repo_id})'
        rake_username = '; repo.root.upstream_username'
        result = run(f"echo '{rake_repo}{rake_username}'|foreman-rake console")
        assert UPSTREAM_USERNAME not in result


class TestScenarioCustomRepoCheck:
    """Scenario test to verify if we can create a custom repository and consume it
    via client then we alter the created custom repository and satellite will be able
    to sync back the repo.

    Test Steps:

        1. Before Satellite upgrade.
        2. Create new Organization and Location.
        3. Create Product, custom repo, cv.
        4. Create activation key and add subscription in it.
        5. Create a content host, register and install package on it.
        6. Upgrade Satellite.
        7. Remove Old package and add new package into custom repo.
        8. Sync repo, publish new version of cv.
        9. Try to install new package on client.

    BZ: 1429201,1698549
    """

    @pre_upgrade
    def test_pre_scenario_custom_repo_check(self):
        """This is pre-upgrade scenario test to verify if we can create a
         custom repository and consume it via content host.

        :id: preupgrade-eb6831b1-c5b6-4941-a325-994a09467478

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization, Location.
            3. Create Product, custom repo, cv.
            4. Create activation key and add subscription.
            5. Create a content host, register and install package on it.

        :expectedresults:

            1. Custom repo is created.
            2. Package is installed on Content host.

        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        lce = entities.LifecycleEnvironment(organization=org).create()

        product = entities.Product(organization=org).create()
        create_repo(rpm1, FILE_PATH)
        repo = entities.Repository(product=product.id, url=CUSTOM_REPO).create()
        repo.sync()

        content_view = publish_content_view(org=org, repolist=repo)
        promote(content_view.version[0], lce.id)

        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            'Packages/b/|grep {}'.format(
                org.label, lce.name, content_view.label, product.label, repo.label, RPM1_NAME
            )
        )

        assert result.return_code == 0
        assert len(result.stdout) >= 1

        subscription = entities.Subscription(organization=org).search(
            query={'search': f'name={product.name}'}
        )[0]
        ak = entities.ActivationKey(
            content_view=content_view, organization=org.id, environment=lce
        ).create()
        ak.add_subscriptions(data={'subscription_id': subscription.id})

        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        client_container_name = [key for key in rhel7_client.keys()][0]

        host_location_update(
            client_container_name=client_container_name, logger_obj=logger, loc=loc
        )
        status = execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager identity',
            host=DOCKER_VM,
        )[DOCKER_VM]
        assert org.name in status
        install_or_update_package(client_hostname=client_container_id, package=RPM1_NAME)

        scenario_dict = {
            self.__class__.__name__: {
                'content_view_name': content_view.name,
                'lce_id': lce.id,
                'lce_name': lce.name,
                'org_label': org.label,
                'prod_label': product.label,
                'rhel_client': rhel7_client,
                'repo_name': repo.name,
            }
        }
        create_dict(scenario_dict)

    @post_upgrade(depend_on=test_pre_scenario_custom_repo_check)
    def test_post_scenario_custom_repo_check(self):
        """This is post-upgrade scenario test to verify if we can alter the
        created custom repository and satellite will be able to sync back
        the repo.

        :id: postupgrade-5c793577-e573-46a7-abbf-b6fd1f20b06e

        :steps:
            1. Remove old and add new package into custom repo.
            2. Sync repo , publish the new version of cv.
            3. Try to install new package on client.


        :expectedresults: Content host should able to pull the new rpm.

        """
        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        content_view_name = entity_data.get('content_view_name')
        lce_id = entity_data.get('lce_id')
        lce_name = entity_data.get('lce_name')
        org_label = entity_data.get('org_label')
        prod_label = entity_data.get('prod_label')
        repo_name = entity_data.get('repo_name')

        create_repo(rpm2, FILE_PATH, post_upgrade=True, other_rpm=rpm1)
        repo = entities.Repository(name=repo_name).search()[0]
        repo.sync()

        content_view = entities.ContentView(name=content_view_name).search()[0]
        content_view.publish()

        content_view = entities.ContentView(name=content_view_name).search()[0]
        promote(content_view.version[-1], lce_id)

        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            'Packages/c/| grep {}'.format(
                org_label, lce_name, content_view.label, prod_label, repo.label, RPM2_NAME
            )
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1
        install_or_update_package(client_hostname=client_container_id, package=RPM2_NAME)
