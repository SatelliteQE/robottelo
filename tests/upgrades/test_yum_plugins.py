"""Test for Loaded yum plugins count related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from fabric.api import execute
from nailgun import entities
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import dockerize
from upgrade_tests.helpers.scenarios import get_entity_data
from wait_for import wait_for

from robottelo.api.utils import attach_custom_product_subscription
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import REPOS
from robottelo.test import APITestCase
from robottelo.test import settings
from robottelo.upgrade_utility import install_or_update_package
from robottelo.upgrade_utility import publish_content_view
from robottelo.upgrade_utility import run_goferd


class TestScenarioYumPluginsCount(APITestCase):
    """The test class contains pre and post upgrade scenarios to test the
    loaded yum plugins count on content host.

    Test Steps:

        1. Before Satellite upgrade.
        2. Create LifecycleEnvironment.
        3. Enable/sync 'base os RHEL7' and tools repos.
        4. Create 'Content View' and activation key.
        5. Create a content host, register and install katello-agent on it.
        6. Upgrade Satellite/Capsule.
        7. Create Product, custom tools repo, sync them.
        8. Attached custom subscription to content host.
        9. Upgrade Katello-agent and restart goferd.
        10. Verifying the loaded yum plugins count.

    BZ: 1625649

    """

    @classmethod
    def setUpClass(cls):
        cls.docker_vm = settings.upgrade.docker_vm
        cls.client_os = DISTRO_RHEL7
        cls.org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        cls.loc = entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]

    def _check_yum_plugins_count(self, client_container_id):
        """Check yum loaded plugins counts """

        kwargs = {'host': self.docker_vm}
        execute(docker_execute_command, client_container_id, 'yum clean all', **kwargs)[
            self.docker_vm
        ]
        plugins_count = execute(
            docker_execute_command,
            client_container_id,
            'yum repolist|grep "Loaded plugins"|wc -l',
            **kwargs,
        )[self.docker_vm]
        self.assertEqual(int(plugins_count), 2)

    def _create_custom_tools_repos(self, product):
        """Create custom tools repo and sync it"""

        tools_repo_url = settings.sattools_repo[DISTRO_RHEL7]
        if None in [tools_repo_url]:
            raise ValueError(f'The Tools Repo URL {self.client_os} is not provided!')

        tools_repo = entities.Repository(
            product=product, content_type='yum', url=tools_repo_url
        ).create()
        call_entity_method_with_timeout(tools_repo.sync, timeout=1400)
        return tools_repo

    def _get_rh_rhel_tools_repos(self):
        """Get list of RHEL7 and tools repos

        :return: nailgun.entities.Repository: repository
        """

        from_version = settings.upgrade.from_version
        repo2_name = 'rhst7_{}'.format(str(from_version).replace('.', ''))

        repo1_id = (
            entities.Repository(organization=self.org)
            .search(query={'search': '{}'.format(REPOS['rhel7']['id'])})[0]
            .id
        )
        repo2_id = (
            entities.Repository(organization=self.org)
            .search(query={'search': '{}'.format(REPOS[repo2_name]['id'])})[0]
            .id
        )

        return [entities.Repository(id=repo_id) for repo_id in [repo1_id, repo2_id]]

    @pre_upgrade
    def test_pre_scenario_yum_plugins_count(self):
        """Create content host and register with Satellite.

        :id: preupgrade-45241ada-c2c4-409e-a6e2-92c2cf0ac16c

        :steps:

            1. Before Satellite upgrade.
            2. Create LifecycleEnvironment.
            3. Enable/sync 'base os RHEL7' and tools repos.
            4. Create 'Content View' and activation key.
            5. Create a content host, register and install katello-agent on it.

        :expectedresults:

            1. The content host is created.
            2. katello-agent install and goferd run.
        """
        environment = entities.LifecycleEnvironment(organization=self.org).search(
            query={'search': 'name=Library'}
        )[0]
        repos = self._get_rh_rhel_tools_repos()
        content_view = publish_content_view(org=self.org, repolist=repos)
        ak = entities.ActivationKey(
            content_view=content_view, organization=self.org.id, environment=environment
        ).create()

        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=self.org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        wait_for(
            lambda: self.org.label
            in execute(
                docker_execute_command,
                client_container_id,
                'subscription-manager identity',
                host=self.docker_vm,
            )[self.docker_vm],
            timeout=800,
            delay=2,
            logger=self.logger,
        )
        status = execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager identity',
            host=self.docker_vm,
        )[self.docker_vm]
        self.assertIn(self.org.label, status)

        install_or_update_package(client_hostname=client_container_id, package="katello-agent")
        run_goferd(client_hostname=client_container_id)

        scenario_dict = {
            self.__class__.__name__: {'rhel_client': rhel7_client, 'cv_id': content_view.id}
        }
        create_dict(scenario_dict)

    @post_upgrade(depend_on=test_pre_scenario_yum_plugins_count)
    def test_post_scenario_yum_plugins_count(self):
        """Upgrade katello agent on pre-upgrade content host registered
        with Satellite.

        :id: postupgrade-45241ada-c2c4-409e-a6e2-92c2cf0ac16c

        :steps:
            1. Create Product, custom tools repo and sync them.
            2. Add in content-view and publish it.
            3. Attach custom subscription to content host.
            4. Update katello-agent and Restart goferd.
            5. Check yum plugins count.

        :expectedresults:
            1. Loaded yum plugins should not load more than two times.
        """

        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        client_container_name = list(client.keys())[0]
        cv = entities.ContentView(id=entity_data.get('cv_id')).read()
        product = entities.Product(organization=self.org).create()

        tools_repo = self._create_custom_tools_repos(product)
        product.sync()

        cv.repository.pop()
        cv.repository.append(tools_repo)
        cv = cv.update(['repository'])
        call_entity_method_with_timeout(cv.publish, timeout=3400)

        attach_custom_product_subscription(prod_name=product.name, host_name=client_container_name)
        install_or_update_package(
            client_hostname=client_container_id, update=True, package="katello-agent"
        )
        run_goferd(client_hostname=client_container_id)
        self._check_yum_plugins_count(client_container_id)
