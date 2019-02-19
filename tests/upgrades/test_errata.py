"""Test for Errata related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Upgrade

:TestType: Functional

:CaseImportance: Low

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
        cls.org = entities.Organization(id=1).read()

    def _run_goferd(self, client_container_id):
        kwargs = {'host': self.docker_vm}
        execute(
            docker_execute_command,
            client_container_id,
            'goferd -f',
            **kwargs
        )

    def _check_package_installed(self, client_container_id, package):
        kwargs = {'host': self.docker_vm}
        docker_execute_command
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -q {}'.format(package),
            **kwargs
        )[self.docker_vm]
        self.assertIn(package, installed_package)

    def _install_package(self, client_container_id, package):
        kwargs = {'host': self.docker_vm}
        execute(
            docker_execute_command,
            client_container_id,
            'yum install -y {}'.format(package),
            **kwargs
        )[self.docker_vm]
        self._check_package_installed(client_container_id, package)

    def _create_custom_rhel_tools_repos(self, client_os, product):
        rhel_repo_url = os.environ.get('{}_CUSTOM_REPO'.format(client_os.upper()))

        tools_repo_url = os.environ.get(
            'TOOLS_{}'.format(client_os.upper()))
        if None in [rhel_repo_url, tools_repo_url]:
            raise ValueError('The Tools Repo URL/RHEL Repo url environment variable for '
                             'OS {} is not provided!'.format(client_os))
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

    @pre_upgrade
    def test_pre_scenario_generate_errata_for_client(self):
        """Create product and repo from which the errata will be generated for the
        Satellite client or content host

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
        client_os = DISTRO_DEFAULT
        # Step 1: Create  Life Cycle Environment, Product and Custom Yum Repo
        environment = entities.LifecycleEnvironment(
            organization=self.org
        ).search(query={'search': 'name=Library'})[0]

        product = entities.Product(organization=self.org).create()
        custom_yum_repo = entities.Repository(product=product,
                                              content_type='yum',
                                              url=FAKE_9_YUM_REPO
                                              ).create()

        # Step 2: Create custom tools, rhel repos and sync them
        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(client_os, product)
        product.sync()
        product = product.read()

        # Step 3: Create content view and publish it
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [custom_yum_repo, tools_repo, rhel_repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        # Step 4: Create activation key and add subscription.
        ak = entities.ActivationKey(
            content_view=content_view,
            organization=self.org.id,
            environment=environment
        ).create()
        subscription = entities.Subscription(organization=self.org).search(query={
            'search': 'name={}'.format(product.name)
        })[0]
        ak.add_subscriptions(data={
            'subscription_id': subscription.id})

        # Step 5: Registering Docker Content Host RHEL7
        rhel7_client = dockerize(
            ak_name=ak.name, distro='rhel7', org_label=self.org.label)
        client_container_id = list(rhel7_client.values())[0]

        # Step 6: Check katello agent and goferd service running on host
        self._install_package(client_container_id, 'katello-agent')
        self._run_goferd(client_container_id)

        # Step 7: Generate Errata by Installing Outdated/Older Packages
        for package in FAKE_9_YUM_OUTDATED_PACKAGES:
            self._install_package(client_container_id, package)
        host = entities.Host().search(query={
            'search': 'activation_key={0}'.format(ak.name)})[0]
        host = host.read()
        applicable_errata_count = host.content_facet_attributes[
            'errata_counts']['total']
        self.assertGreater(applicable_errata_count, 1)

        # Step 8: Collect the erratum list
        erratum_list = entities.Errata(repository=custom_yum_repo).search(query={
            'order': 'updated ASC',
            'per_page': 1000,
        })
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))
        scenario_dict = {self.__class__.__name__: {
            'rhel_client': rhel7_client,
            'activation_key': ak.name,
            'custom_repo_id': custom_yum_repo.id
        }}
        create_dict(scenario_dict)

    @post_upgrade
    def test_post_scenario_errata_count_installtion(self):
        """Post-upgrade scenario that installs the package on pre-upgrade
        client remotely and then verifies if the package installed

        :id: 88fd28e6-b4df-46c0-91d6-784859fd1c21

        :steps:

            1. Recovered pre_upgrade data for post_upgrade verification
            2. Verifying errata count has not changed on satellite
            3. Run goferd
            4. Verifying the errata_ids
            5. Verifying installation errata passes successfully
            6. Verifying that package installation passed successfully by remote docker exec

        :expectedresults:
            1. errata count, erratum list should same after satellite upgrade
            2. Installation of errata should be pass successfully
         """
        # Step 1: Recovered all required data for post_upgrade verification
        entity_data = get_entity_data(self.__class__.__name__)

        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        custom_repo_id = entity_data.get('custom_repo_id')
        custom_yum_repo = entities.Repository(id=custom_repo_id).read()
        activation_key = entity_data.get('activation_key')
        host = entities.Host().search(query={
            'search': 'activation_key={0}'.format(activation_key)})[0]
        host = host.read()
        applicable_errata_count = host.content_facet_attributes[
            'errata_counts']['total']

        # Step 2: Verifying errata count has not changed on satellite
        self.assertGreater(applicable_errata_count, 1)
        erratum_list = entities.Errata(repository=custom_yum_repo).search(query={
            'order': 'updated ASC',
            'per_page': 1000,
        })

        # Step 3: Run goferd
        self._run_goferd(client_container_id)

        # Step 4: Verifying the errata_ids
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))

        # Step 5: Verifying installation errata passes successfully
        for errata in FAKE_9_YUM_ERRATUM:
            host.errata_apply(data={'errata_ids': [errata]})
            host = host.read()
            applicable_errata_count -= 1
        self.assertEqual(
            host.content_facet_attributes['errata_counts']['total'],
            0
        )

        # Step 6 : Verify that package installation passed successfully
        for package in FAKE_9_YUM_UPDATED_PACKAGES:
            self._check_package_installed(client_container_id, package)
