"""Test for Errata related Upgrade Scenario's

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

from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import FAKE_9_YUM_ERRATUM
from robottelo.constants import FAKE_9_YUM_OUTDATED_PACKAGES
from robottelo.constants import FAKE_9_YUM_UPDATED_PACKAGES
from robottelo.constants import REPOS
from robottelo.constants.repos import FAKE_9_YUM_REPO
from robottelo.test import APITestCase
from robottelo.test import settings
from robottelo.upgrade_utility import host_location_update
from robottelo.upgrade_utility import install_or_update_package
from robottelo.upgrade_utility import publish_content_view
from robottelo.upgrade_utility import run_goferd


class Test_scenarioErrataAbstract:
    """This is an Abstract Class whose methods are inherited by others errata
    scenarios"""

    def _errata_count(self, ak):
        """fetch the content host details.
        :param: str ak: The activation key name
        :return: int installable_errata_count : installable_errata count
        """
        host = entities.Host().search(query={'search': f'activation_key={ak}'})[0]
        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        return installable_errata_count

    def _create_custom_rhel_tools_repos(self, product):
        """Install packge on docker content host."""
        rhel_repo_url = settings.rhel7_os
        tools_repo_url = settings.sattools_repo[DISTRO_RHEL7]
        if None in [rhel_repo_url, tools_repo_url]:
            raise ValueError('The rhel7_os or tools_rhel7 Repo url is not set in settings!')
        tools_repo = entities.Repository(
            product=product, content_type='yum', url=tools_repo_url
        ).create()
        rhel_repo = entities.Repository(
            product=product, content_type='yum', url=rhel_repo_url
        ).create()
        call_entity_method_with_timeout(rhel_repo.sync, timeout=3000)
        call_entity_method_with_timeout(tools_repo.sync, timeout=3000)
        return tools_repo, rhel_repo

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


class Test_scenario_errata_count(APITestCase, Test_scenarioErrataAbstract):
    """The test class contains pre and post upgrade scenarios to test if the
    errata count for satellite client/content host.

    Test Steps::

        1. Before Satellite upgrade, Create a content host and register it with
            satellite
        2. Install packages and down-grade them to generate errata for a client
        3. Store Errata count and details in file
        4. Upgrade Satellite
        5. Check if the Errata Count in Satellite after the upgrade.
    """

    @classmethod
    def setUpClass(cls):
        cls.docker_vm = settings.upgrade.docker_vm
        cls.client_os = DISTRO_RHEL7

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
            2. errata count, erratum list will be generated to satellite client/content
                host

        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        environment = entities.LifecycleEnvironment(organization=org).search(
            query={'search': 'name=Library'}
        )[0]

        product = entities.Product(organization=org).create()
        custom_yum_repo = entities.Repository(
            product=product, content_type='yum', url=FAKE_9_YUM_REPO
        ).create()
        product.sync()

        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        repolist = [custom_yum_repo, tools_repo, rhel_repo]
        content_view = publish_content_view(org=org, repolist=repolist)
        ak = entities.ActivationKey(
            content_view=content_view, organization=org.id, environment=environment
        ).create()
        subscription = entities.Subscription(organization=org).search(
            query={'search': f'name={product.name}'}
        )[0]

        ak.add_subscriptions(data={'subscription_id': subscription.id})
        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = list(rhel7_client.values())[0]
        client_container_name = [key for key in rhel7_client.keys()][0]
        host_location_update(
            client_container_name=client_container_name, logger_obj=self.logger, loc=loc
        )
        wait_for(
            lambda: org.name
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
        install_or_update_package(client_hostname=client_container_id, package="katello-agent")
        run_goferd(client_hostname=client_container_id)

        for package in FAKE_9_YUM_OUTDATED_PACKAGES:
            install_or_update_package(client_hostname=client_container_id, package=package)

        host = entities.Host().search(query={'search': f'activation_key={ak.name}'})[0]
        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        self.assertGreater(installable_errata_count, 1)
        erratum_list = entities.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))
        scenario_dict = {
            self.__class__.__name__: {
                'rhel_client': rhel7_client,
                'activation_key': ak.name,
                'custom_repo_id': custom_yum_repo.id,
                'product_id': product.id,
                'conten_view_id': content_view.id,
            }
        }
        create_dict(scenario_dict)

    @post_upgrade(depend_on=test_pre_scenario_generate_errata_for_client)
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
            6. Verifying that package installation passed successfully by remote docker
                exec

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
        host = entities.Host().search(query={'search': f'activation_key={activation_key}'})[0]

        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        tools_repo, rhel_repo = self._create_custom_rhel_tools_repos(product)
        call_entity_method_with_timeout(product.sync, timeout=1400)
        for repo in (tools_repo, rhel_repo):
            content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()
        install_or_update_package(
            client_hostname=client_container_id, update=True, package="katello-agent"
        )

        run_goferd(client_hostname=client_container_id)
        self.assertGreater(installable_errata_count, 1)

        erratum_list = entities.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))

        for errata in FAKE_9_YUM_ERRATUM:
            host.errata_apply(data={'errata_ids': [errata]})
            installable_errata_count -= 1

        # waiting for errata count to become 0, as profile uploading take some
        # amount of time
        wait_for(
            lambda: self._errata_count(ak=activation_key) == 0,
            timeout=400,
            delay=2,
            logger=self.logger,
        )
        host = entities.Host().search(query={'search': f'activation_key={activation_key}'})[0]
        self.assertEqual(host.content_facet_attributes['errata_counts']['total'], 0)
        for package in FAKE_9_YUM_UPDATED_PACKAGES:
            install_or_update_package(client_hostname=client_container_id, package=package)


class Test_scenario_errata_count_with_previous_version_katello_agent(
    APITestCase, Test_scenarioErrataAbstract
):
    """The test class contains pre and post upgrade scenarios to test erratas count
    and remotely install using n-1 'katello-agent' on content host.

    Test Steps:

        1. Before Satellite upgrade, Create a content host and register it with
            Satellite
        2. Install packages and down-grade them to generate errata.
        3. Upgrade Satellite
        4. Check if the Erratas Count in Satellite after the upgrade.
        5. Install erratas remotely on content host and check the erratas count.

    BZ: 1529682
    """

    @classmethod
    def setUpClass(cls):
        cls.docker_vm = settings.upgrade.docker_vm
        cls.client_os = DISTRO_RHEL7
        cls.org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        cls.loc = entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]

    @pre_upgrade
    def test_pre_scenario_generate_errata_with_previous_version_katello_agent_client(self):
        """Create product and repo from which the errata will be generated for the
        Satellite client or content host.

        :id: preupgrade-4e515f84-2582-4b8b-a625-9f6c6966aa59

        :steps:

            1. Create Life Cycle Environment, Product and Custom Yum Repo.
            2. Enable/sync 'base os RHEL7' and tools repos.
            3. Create a content view and publish it.
            4. Create activation key and add subscription.
            5. Registering Docker Content Host RHEL7.
            6. Install and check katello agent and goferd service running on host.
            7. Generate Errata by Installing Outdated/Older Packages.
            8. Collect the Erratum list.

        :expectedresults:

            1. The content host is created.
            2. errata count, erratum list will be generated to satellite client/content host.

        """
        environment = entities.LifecycleEnvironment(organization=self.org).search(
            query={'search': 'name=Library'}
        )[0]

        product = entities.Product(organization=self.org).create()
        custom_yum_repo = entities.Repository(
            product=product, content_type='yum', url=FAKE_9_YUM_REPO
        ).create()
        call_entity_method_with_timeout(product.sync, timeout=1400)

        repos = self._get_rh_rhel_tools_repos()
        repos.append(custom_yum_repo)
        content_view = publish_content_view(org=self.org, repolist=repos)
        custom_sub = entities.Subscription(organization=self.org).search(
            query={'search': f'name={product.name}'}
        )[0]
        rh_sub = entities.Subscription(organization=1).search(
            query={'search': f'{DEFAULT_SUBSCRIPTION_NAME}'}
        )[0]

        ak = entities.ActivationKey(
            content_view=content_view,
            organization=self.org.id,
            environment=environment,
            auto_attach=False,
        ).create()
        ak.add_subscriptions(data={'subscription_id': custom_sub.id})
        ak.add_subscriptions(data={'subscription_id': rh_sub.id})

        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=self.org.label)
        client_container_id = list(rhel7_client.values())[0]

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

        # Update OS to make errata count 0
        execute(docker_execute_command, client_container_id, 'yum update -y', host=self.docker_vm)[
            self.docker_vm
        ]
        install_or_update_package(client_hostname=client_container_id, package="katello-agent")
        run_goferd(client_hostname=client_container_id)

        for package in FAKE_9_YUM_OUTDATED_PACKAGES:
            install_or_update_package(client_hostname=client_container_id, package=package)
        host = entities.Host().search(query={'search': f'activation_key={ak.name}'})[0]

        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        self.assertGreater(installable_errata_count, 1)

        erratum_list = entities.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))
        scenario_dict = {
            self.__class__.__name__: {
                'rhel_client': rhel7_client,
                'activation_key': ak.name,
                'custom_repo_id': custom_yum_repo.id,
                'product_id': product.id,
            }
        }
        create_dict(scenario_dict)

    @post_upgrade(
        depend_on=test_pre_scenario_generate_errata_with_previous_version_katello_agent_client
    )
    def test_post_scenario_generate_errata_with_previous_version_katello_agent_client(self):
        """Post-upgrade scenario that installs the package on pre-upgraded client
        remotely and then verifies if the package installed and errata counts.

        :id: postupgrade-b61f8f5a-44a3-4d3e-87bb-fc399e03ba6f

        :steps:

            1. Recovered pre_upgrade data for post_upgrade verification.
            2. Verifying errata count has not changed on satellite.
            3. Restart goferd/Katello-agent running.
            4. Verifying the errata_ids.
            5. Verifying installation errata passes successfully.
            6. Verifying that package installation passed successfully by remote docker
                exec.

        :expectedresults:
            1. errata count, erratum list should same after satellite upgrade.
            2. Installation of errata should be pass successfully and check errata counts
                is 0.
        """

        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        custom_repo_id = entity_data.get('custom_repo_id')
        custom_yum_repo = entities.Repository(id=custom_repo_id).read()
        activation_key = entity_data.get('activation_key')
        host = entities.Host().search(query={'search': f'activation_key={activation_key}'})[0]

        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        self.assertGreater(installable_errata_count, 1)

        erratum_list = entities.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        self.assertEqual(sorted(errata_ids), sorted(FAKE_9_YUM_ERRATUM))

        for errata in FAKE_9_YUM_ERRATUM:
            host.errata_apply(data={'errata_ids': [errata]})

        for package in FAKE_9_YUM_UPDATED_PACKAGES:
            install_or_update_package(client_hostname=client_container_id, package=package)

        # waiting for errata count to become 0, as profile uploading take some
        # amount of time
        wait_for(
            lambda: self._errata_count(ak=activation_key) == 0,
            timeout=400,
            delay=2,
            logger=self.logger,
        )
        self.assertEqual(self._errata_count(ak=activation_key), 0)
