"""Test for Loaded yum plugins count related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from wait_for import wait_for

from fabric.api import execute
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    attach_custom_product_subscription,
    call_entity_method_with_timeout,
    enable_sync_redhat_repo,
    upload_manifest,
)
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DISTRO_RHEL7,
    REPOS,
)
from robottelo.test import APITestCase, settings
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import (
    create_dict,
    dockerize,
    get_entity_data
)


class Scenario_yum_plugins_count(APITestCase):
    """The test class contains pre and post upgrade scenarios to test the
    loaded yum plugins count on content host.

    Test Steps:

        1. Before Satellite upgrade.
        2. Create Organization, Location and LifecycleEnvironment.
        3. Upload Manifest, enable/sync 'base os RHEL7' and tools repos.
        4. Create 'Content View' and activation key.
        5. Create a content host, register and install katello-agent on it.
        6. Upgrade Satellite/Capsule.
        7. Create Product, custom tools repo, sync them.
        8  Attached custom subscription to content host.
        9. Upgrade Katello-agent and restart goferd.
        10. Verifying the loaded yum plugins count.

    BZ: 1625649

    """
    @classmethod
    def setUpClass(cls):
        cls.docker_vm = settings.upgrade.docker_vm
        cls.client_os = DISTRO_RHEL7

    def _run_goferd(self, client_container_id):
        """Start the goferd process."""

        kwargs = {'async': True, 'host': self.docker_vm}
        execute(
            docker_execute_command,
            client_container_id,
            'pkill -f gofer',
            **kwargs
        )
        execute(
            docker_execute_command,
            client_container_id,
            'goferd -f',
            **kwargs
        )
        status = execute(docker_execute_command, client_container_id, 'ps -aux',
                         host=self.docker_vm)[self.docker_vm]
        self.assertIn('goferd', status)

    def _check_yum_plugins_count(self, client_container_id):
        """Check yum loaded plugins counts """

        kwargs = {'host': self.docker_vm}
        execute(docker_execute_command, client_container_id,
                'yum clean all', **kwargs)[self.docker_vm]
        plugins_count = execute(
            docker_execute_command,
            client_container_id,
            'yum repolist|grep "Loaded plugins"|wc -l',
            **kwargs)[self.docker_vm]
        self.assertEqual(int(plugins_count), 2)

    def _check_package_installed(self, client_container_id, package):
        """Verify if package is installed on docker content host."""

        kwargs = {'host': self.docker_vm}
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'yum list installed {}'.format(package),
            **kwargs
        )[self.docker_vm]
        self.assertIn(package, installed_package)

    def _install_or_update_package(self, client_container_id, package, update=False):
        """Install/update the package on docker content host."""

        kwargs = {'host': self.docker_vm}
        execute(docker_execute_command,
                client_container_id,
                'subscription-manager repos --enable=*;yum clean all',
                **kwargs)[self.docker_vm]
        if update:
            command = 'yum update -y {}'.format(package)
        else:
            command = 'yum install -y {}'.format(package)

        execute(docker_execute_command, client_container_id, command, **kwargs)[self.docker_vm]
        self._check_package_installed(client_container_id, package)

    def _create_custom_tools_repos(self, product):
        """Create custom tools repo and sync it"""

        tools_repo_url = settings.sattools_repo[DISTRO_RHEL7]
        if None in [tools_repo_url]:
            raise ValueError('The Tools Repo URL {} is not provided!'.format(self.client_os))

        tools_repo = entities.Repository(product=product,
                                         content_type='yum',
                                         url=tools_repo_url
                                         ).create()
        call_entity_method_with_timeout(tools_repo.sync, timeout=1400)
        return tools_repo

    def _host_status(self, client_container_name=None):
        """ fetch the content host details.

        :param: str client_container_name: The content host hostname
        :return: nailgun.entity.host: host
        """
        host = entities.Host().search(
            query={'search': '{0}'.format(client_container_name)})
        return host

    def _host_location_update(self, client_container_name=None, loc=None):
        """ Check the content host status (as package profile update task does take time to
        upload) and update location.

        :param: str client_container_name: The content host hostname
        :param: str loc: Location
        """

        if len(self._host_status(client_container_name=client_container_name)) == 0:
            wait_for(
                lambda: len(self._host_status(client_container_name=client_container_name)) > 0,
                timeout=100,
                delay=2,
                logger=self.logger
            )
        host_loc = self._host_status(client_container_name=client_container_name)[0]
        host_loc.location = loc
        host_loc.update(['location'])
        self.assertEqual(loc.name, host_loc.location.name)

    def _publish_content_view(self, org, repolist):
        """publish content view and return content view"""

        content_view = entities.ContentView(organization=org).create()
        content_view.repository = repolist
        content_view = content_view.update(['repository'])
        call_entity_method_with_timeout(content_view.publish, timeout=3400)
        content_view = content_view.read()
        return content_view

    def _create_rh_rhel_tools_repos(self, org_id):
        """ Upload manifest, enable RHEL7 and tools repos
        and sync them

        :param: int org_id: Organization ID

        :return: nailgun.entities.Repository: repository
        """

        from_version = settings.upgrade.from_version
        repo_name = 'rhst7_{}'.format(str(from_version).replace('.', ''))
        rh_rhel = {
            'name': REPOS['rhel7']['name'],
            'product': REPOS['rhel7']['product'],
            'reposet': REPOS['rhel7']['reposet'],
            'basearch': REPOS['rhel7']['arch'],
            'releasever': '7Server',
        }
        rh_tools = {
            'name': REPOS[repo_name]['name'],
            'product': REPOS[repo_name]['product'],
            'reposet': REPOS[repo_name]['reposet'],
            'basearch': DEFAULT_ARCHITECTURE,
            'releasever': '7Server',
        }
        with manifests.clone() as manifest:
            upload_manifest(org_id, manifest.content)
            repo1_id = enable_sync_redhat_repo(rh_rhel, org_id)
            repo2_id = enable_sync_redhat_repo(rh_tools, org_id)

        return [entities.Repository(id=repo_id) for repo_id in [repo1_id, repo2_id]]

    @pre_upgrade
    def test_pre_scenario_yum_plugins_count(self):
        """Create content host and register with Satellite.

        :id: preupgrade-45241ada-c2c4-409e-a6e2-92c2cf0ac16c

        :steps:

            1. Before Satellite upgrade.
            2. Create Organization, Location and LifecycleEnvironment.
            3. Upload Manifest, enable/sync 'base os RHEL7' and tools repos.
            4. Create 'Content View' and activation key.
            5. Create a content host, register and install katello-agent on it.

        :expectedresults:

            1. The content host is created.
            2. katello-agent install and goferd run.
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()

        environment = entities.LifecycleEnvironment(organization=org
                                                    ).search(query={'search': 'name=Library'})[0]
        repos = self._create_rh_rhel_tools_repos(org.id)
        content_view = self._publish_content_view(org=org, repolist=repos)
        ak = entities.ActivationKey(content_view=content_view,
                                    organization=org.id,
                                    environment=environment).create()

        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        client_container_name = [key for key in rhel7_client.keys()][0]

        self._host_location_update(client_container_name=client_container_name, loc=loc)
        wait_for(
            lambda: org.name in execute(docker_execute_command,
                                        client_container_id,
                                        'subscription-manager identity',
                                        host=self.docker_vm)[self.docker_vm],
            timeout=100,
            delay=2,
            logger=self.logger
        )
        status = execute(docker_execute_command,
                         client_container_id,
                         'subscription-manager identity',
                         host=self.docker_vm)[self.docker_vm]
        self.assertIn(org.name, status)

        self._install_or_update_package(client_container_id, 'katello-agent')
        self._run_goferd(client_container_id)

        scenario_dict = {self.__class__.__name__: {
            'org_id': org.id,
            'rhel_client': rhel7_client,
            'cv_id': content_view.id
        }}
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
        org = entities.Organization(id=entity_data.get('org_id')).read()
        product = entities.Product(organization=org).create()

        tools_repo = self._create_custom_tools_repos(product)
        product.sync()

        cv.repository.pop()
        cv.repository.append(tools_repo)
        cv = cv.update(['repository'])
        call_entity_method_with_timeout(cv.publish, timeout=3400)

        attach_custom_product_subscription(prod_name=product.name,
                                           host_name=client_container_name)
        self._install_or_update_package(client_container_id, "katello-agent", update=True)
        self._run_goferd(client_container_id)
        self._check_yum_plugins_count(client_container_id)
