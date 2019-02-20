"""Test for Errata related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import os

from fabric.api import execute
from nailgun import entities
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.constants import (
    DISTRO_DEFAULT,
    FAKE_9_YUM_ERRATUM,
    FAKE_9_YUM_OUTDATED_PACKAGES,
    FAKE_9_YUM_REPO,
    FAKE_9_YUM_UPDATED_PACKAGES
)
from robottelo.test import APITestCase
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import (
    create_dict,
    dockerize,
    get_entity_data
)


class Scenario_errata_count(APITestCase):
    """The test class contains pre and post upgrade scenarios to test if the
    errata count for satellite client/content host.

    Test Steps:

        1. Before Satellite upgrade, Create a content host and register it with
            satellite
        2. Install packages and down-grade them to generate errata for a client
        3. Store Errata count and details in file
        4. Upgrade Satellite
        5. Check if the Errata Count in Satellite after the upgrade.
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

    def _check_package_installed(self, client_container_id, package):
        """Verify if packge is installed on docker content host."""
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
        """Install packge on docker content host."""
        kwargs = {'host': self.docker_vm}
        if update:
            command = 'yum update -y {}'.format(package)
        else:
            command = 'yum install -y {}'.format(package)
        execute(
            docker_execute_command,
            client_container_id,
            command,
            **kwargs
        )[self.docker_vm]
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

    def _publish_content_view(self, org, repolist):
        """publish content view and return content view"""
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = repolist
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        return content_view

    @pre_upgrade
    def test_pre_scenario_generate_errata_for_client(self):
        """Create product and repo from which the errata will be generated for the
        Satellite client or content host.

        :id: 88fd28e6-b4df-46c0-91d6-784859fd1c21

        :steps:

            1. Create  Life Cycle Environment, Product and Custom Yum Repo
            2. Create custom tools, rhel repos and sync them
            3. Create content view and publish it
            4. Create activation key and add subscription.
            5. Registering Docker Content Host RHEL7
            6. Check katello agent and goferd service running on host
            7. Generate Errata by Installing Outdated/Older Packages
            8. Collect the Erratum list


        :expectedresults:

            1. The content host is created
            2. errata count, erratum list will be generated to satellite client/content host

        """
        org = entities.Organization().create()
        environment = entities.LifecycleEnvironment(
            organization=org
        ).search(query={'search': 'name=Library'})[0]

        product = entities.Product(organization=org).create()
        custom_yum_repo = entities.Repository(product=product,
                                              content_type='yum',
                                              url=FAKE_9_YUM_REPO
                                              ).create()

        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        product.sync()
        repolist = [custom_yum_repo, tools_repo, rhel_repo]
        content_view = self._publish_content_view(org=org, repolist=repolist)
        ak = entities.ActivationKey(
            content_view=content_view,
            organization=org.id,
            environment=environment
        ).create()
        subscription = entities.Subscription(organization=org).search(query={
            'search': 'name={}'.format(product.name)
        })[0]

        ak.add_subscriptions(data={
            'subscription_id': subscription.id})
        rhel7_client = dockerize(
            ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = list(rhel7_client.values())[0]
        self._install_or_update_package(client_container_id, 'katello-agent')
        self._run_goferd(client_container_id)

        for package in FAKE_9_YUM_OUTDATED_PACKAGES:
            self._install_or_update_package(client_container_id, package)
        host = entities.Host().search(query={
            'search': 'activation_key={0}'.format(ak.name)})[0]
        applicable_errata_count = host.content_facet_attributes[
            'errata_counts']['total']
        self.assertGreater(applicable_errata_count, 1)
        erratum_list = entities.Errata(repository=custom_yum_repo).search(query={
            'order': 'updated ASC',
            'per_page': 1000,
        })
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))
        scenario_dict = {self.__class__.__name__: {
            'rhel_client': rhel7_client,
            'activation_key': ak.name,
            'custom_repo_id': custom_yum_repo.id,
            'product_id': product.id,
            'conten_view_id': content_view.id
        }}
        create_dict(scenario_dict)

    @post_upgrade
    def test_post_scenario_errata_count_installtion(self):
        """Post-upgrade scenario that installs the package on pre-upgrade
        client remotely and then verifies if the package installed.

        :id: 88fd28e6-b4df-46c0-91d6-784859fd1c21

        :steps:

            1. Recovered pre_upgrade data for post_upgrade verification
            2. Verifying errata count has not changed on satellite
            3. Update Katello-agent and Restart goferd
            4. Verifying the errata_ids
            5. Verifying installation errata passes successfully
            6. Verifying that package installation passed successfully by remote docker exec

        :expectedresults:
            1. errata count, erratum list should same after satellite upgrade
            2. Installation of errata should be pass successfully
         """
        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        custom_repo_id = entity_data.get('custom_repo_id')
        product_id = entity_data.get('product_id')
        conten_view_id = entity_data.get('conten_view_id')
        product = entities.Product(id=product_id).read()
        content_view = entities.ContentView(id=conten_view_id).read()
        custom_yum_repo = entities.Repository(id=custom_repo_id).read()
        activation_key = entity_data.get('activation_key')
        host = entities.Host().search(query={
            'search': 'activation_key={0}'.format(activation_key)})[0]

        applicable_errata_count = host.content_facet_attributes[
            'errata_counts']['total']
        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        product.sync()
        for repo in (tools_repo, rhel_repo):
            content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        self._install_or_update_package(client_container_id,
                                        "katello-agent",
                                        update=True)
        self._run_goferd(client_container_id)
        self.assertGreater(applicable_errata_count, 1)

        erratum_list = entities.Errata(repository=custom_yum_repo).search(query={
            'order': 'updated ASC',
            'per_page': 1000,
        })
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))

        for errata in FAKE_9_YUM_ERRATUM:
            host.errata_apply(data={'errata_ids': [errata]})
            applicable_errata_count -= 1
        self.assertEqual(
            host.content_facet_attributes['errata_counts']['total'],
            0
        )
        for package in FAKE_9_YUM_UPDATED_PACKAGES:
            self._check_package_installed(client_container_id, package)
