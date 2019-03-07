"""Test for Loaded yum plugins count related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import os
from wait_for import wait_for

from fabric.api import execute
from nailgun import entities
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.constants import DISTRO_DEFAULT
from robottelo.test import APITestCase
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
        2. Create new Organization and Location.
        3. Create Product, custom tools, rhel repos and sync them.
        4. Create activation key and add subscription.
        5. Create a content host, register and install katello-agent on it.
        6. Upgrade Satellite/Capsule.
        7. Upgrade Katello-agent and restart goferd.
        8. Verifying the loaded yum plugins count.

    BZ: 1625649

    """
    @classmethod
    def setUpClass(cls):
        cls.docker_vm = os.environ.get('DOCKER_VM')
        cls.client_os = DISTRO_DEFAULT

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
            **kwargs
        )[self.docker_vm]
        self.assertEqual(int(plugins_count), 2)

    def _check_package_installed(self, client_container_id, package):
        """Verify if package is installed on docker content host."""
        kwargs = {'host': self.docker_vm}
        docker_execute_command
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -q {}'.format(package),
            **kwargs
        )[self.docker_vm]
        self.assertIn(package, installed_package)

    def _install_or_update_package(self, client_container_id, package, update=False):
        """Install/update the package on docker content host."""
        kwargs = {'host': self.docker_vm}
        execute(docker_execute_command, client_container_id,
                'subscription-manager repos;yum clean all', **kwargs)[self.docker_vm]
        if update:
            command = 'yum update -y {}'.format(package)
        else:
            command = 'yum install -y {}'.format(package)
        execute(docker_execute_command, client_container_id, command, **kwargs)[self.docker_vm]
        self._check_package_installed(client_container_id, package)

    def _create_custom_rhel_tools_repos(self, product):
        """Install packge on docker content host."""
        rhel_repo_url = os.environ.get('{}_CUSTOM_REPO'.format(self.client_os.upper()))

        tools_repo_url = os.environ.get(
            'TOOLS_{}'.format(self.client_os.upper()))
        if None in [rhel_repo_url, tools_repo_url]:
            raise ValueError('The Tools Repo URL/RHEL Repo url environment variable for '
                             'OS {} is not provided!'.format(self.client_os))
        tools_repo = entities.Repository(product=product,
                                         content_type='yum',
                                         url=tools_repo_url
                                         ).create()
        rhel_repo = entities.Repository(product=product,
                                        content_type='yum',
                                        url=rhel_repo_url,
                                        ).create()
        call_entity_method_with_timeout(rhel_repo.sync, timeout=1400)
        return tools_repo, rhel_repo

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

    def _publish_content_view(self, org, repolist):
        """publish content view and return content view"""
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = repolist
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        return content_view

    @pre_upgrade
    def test_pre_scenario_yum_plugins_count(self):
        """Create content host and register with Satellite.

        :id: preupgrade-45241ada-c2c4-409e-a6e2-92c2cf0ac16c

        :steps:

            1. Before Satellite upgrade.
            2. Create new Organization and Location.
            3. Create Product, custom tools, rhel repos and sync them.
            4. Create activation key and add subscription.
            5. Create a content host, register and install katello-agent on it.

        :expectedresults:

            1. The content host is created.
            2. katello-agent install and goferd run.
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()

        environment = entities.LifecycleEnvironment(organization=org
                                                    ).search(query={'search': 'name=Library'})[0]
        product = entities.Product(organization=org).create()
        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        product.sync()
        repolist = [tools_repo, rhel_repo]
        content_view = self._publish_content_view(org=org, repolist=repolist)

        ak = entities.ActivationKey(content_view=content_view, organization=org.id,
                                    environment=environment).create()
        subscription = entities.Subscription(organization=org).search(query={
            'search': 'name={}'.format(product.name)})[0]

        ak.add_subscriptions(data={'subscription_id': subscription.id})
        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        client_container_name = [key for key in rhel7_client.keys()][0]
        self._host_location_update(client_container_name=client_container_name, loc=loc)

        status = execute(docker_execute_command, client_container_id,
                         'subscription-manager identity', host=self.docker_vm)[self.docker_vm]
        self.assertIn(org.name, status)

        self._install_or_update_package(client_container_id, 'katello-agent')
        self._run_goferd(client_container_id)

        scenario_dict = {self.__class__.__name__: {
            'rhel_client': rhel7_client,
            'product_id': product.id,
            'conten_view_id': content_view.id
        }}
        create_dict(scenario_dict)

    @post_upgrade
    def test_post_scenario_yum_plugins_count(self):
        """Upgrade katello agent on pre-upgrade content host registered
        with Satellite.

        :id: postupgrade-45241ada-c2c4-409e-a6e2-92c2cf0ac16c

        :steps:
            1. Create custom tool repo as per upgraded Satellite version and sync.
            2. Add in content-view and publish it.
            2. Update Katello-agent and Restart goferd.
            2. Check yum plugins count.

        :expectedresults:
            1. Loaded yum plugins should not load more than two times.
         """
        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        product_id = entity_data.get('product_id')
        conten_view_id = entity_data.get('conten_view_id')
        product = entities.Product(id=product_id).read()
        content_view = entities.ContentView(id=conten_view_id).read()

        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        product.sync()
        for repo in (tools_repo, rhel_repo):
            content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()

        self._install_or_update_package(client_container_id, "katello-agent", update=True)
        self._run_goferd(client_container_id)
        self._check_yum_plugins_count(client_container_id)
