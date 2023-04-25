"""Test for Errata related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ErrataManagement

:team: Phoenix-content

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from broker import Broker
from wait_for import wait_for

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import ContentHost
from robottelo.logging import logger


class TestScenarioErrataAbstract:
    """This is an Abstract Class whose methods are inherited by others errata
    scenarios"""

    def _create_custom_rhel_n_client_repos(self, target_sat, product, v_major):
        """Create custom RHEL (system) and Satellite Client repos and sync them"""
        repos = []
        rhel_repo_urls = [settings.repos[f'rhel{v_major}_os']]
        if v_major > 7:
            rhel_repo_urls = [rhel_repo_urls[0]['BASEOS'], rhel_repo_urls[0]['APPSTREAM']]

        client_repo_url = settings.repos.satclient_repo[f'rhel{v_major}']
        if not all([all(rhel_repo_urls), client_repo_url]):
            raise ValueError(
                f'Repo URLs for RHEL {v_major} system repository or/and '
                f'Satellite Client repository for RHEL {v_major} are not set.'
            )
        # Satellite Client repo
        repos.append(
            target_sat.api.Repository(
                product=product, content_type='yum', url=client_repo_url
            ).create()
        )
        # RHEL system repo(s)
        for url in rhel_repo_urls:
            repos.append(
                target_sat.api.Repository(product=product, content_type='yum', url=url).create()
            )

        for repo in repos:
            repo.sync(timeout=3000)
        return repos

    def _get_rh_rhel_n_client_repos(self, target_sat, org, rhel_client):
        """Get list of RHEL (system) and Satellite Client repository IDs

        This method assumes that the RHEL and Satellite Client repositories
        are already created and synced.

        :return: List[entities.Repository]: repositories
        """
        rhel_repo_labels = (
            ['rhel_bos', 'rhel_aps'] if rhel_client.os_version.major > 7 else ['rhel']
        )
        rhel_repos = [
            target_sat.api.Repository(organization=org).search(
                query={'search': rhel_client.REPOS[repo]['id']}
            )[0]
            for repo in rhel_repo_labels
        ]
        sat_client_repo = target_sat.api.Repository(organization=org).search(
            query={'search': rhel_client.REPOS[constants.PRODUCT_KEY_SAT_CLIENT]['id']}
        )[0]

        return [*rhel_repos, sat_client_repo]

    def _check_yum_plugins_count(self, host):
        """Check yum loaded plugins message count"""
        host.execute('yum clean all')
        plugins_count = host.execute('yum repolist | grep "Loaded plugins" | wc -l').stdout
        # The 'Loaded plugins' can happen once or (in the case of enabled repository upload) twice.
        assert int(plugins_count) <= 2, 'Loaded plugins message is displayed more than twice'


class TestScenarioErrataCount(TestScenarioErrataAbstract):
    """The test class contains pre and post upgrade scenarios to test errata
    applicability and errata count on Satellite content host.

    Test Steps::

        1. Before Satellite upgrade, Create a content host and register it with
            Satellite
        2. Install packages and down-grade them to generate errata for a client
        3. Store Errata count and details in file
        4. Upgrade Satellite
        5. Check if the Errata Count in Satellite after the upgrade.
    """

    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.no_containers
    @pytest.mark.pre_upgrade
    def test_pre_scenario_generate_errata_for_client(
        self, target_sat, rhel_contenthost, function_org, save_test_data
    ):
        """Create product and repo from which the errata will be generated for the
        Satellite content host.

        :id: preupgrade-88fd28e6-b4df-46c0-91d6-784859fd1c21

        :steps:

            1. Create Product and Custom Yum Repo
            2. Create custom tools, rhel repos and sync them
            3. Create content view and publish it
            4. Create activation key and add subscription
            5. Register RHEL host to Satellite
            7. Generate Errata by installing outdated/older packages
            8. Check that errata applicability generated expected errata list for the given client.

        :expectedresults:

            1. The content host is created
            2. errata count, erratum list will be generated to Satellite content host
            3. All the expected errata are ready-to-be-applied on the client

        :BZ: 1625649

        :customerscenario: true
        """
        rhel_contenthost._skip_context_checkin = True
        environment = target_sat.api.LifecycleEnvironment(organization=function_org).search(
            query={'search': f'name={constants.ENVIRONMENT}'}
        )[0]
        product = target_sat.api.Product(organization=function_org).create()
        custom_yum_repo = target_sat.api.Repository(
            product=product, content_type='yum', url=settings.repos.yum_9.url
        ).create()
        product.sync()
        synced_repos = self._create_custom_rhel_n_client_repos(
            target_sat, product, rhel_contenthost.os_version.major
        )
        repolist = [
            custom_yum_repo,
            *synced_repos,
        ]
        content_view = target_sat.publish_content_view(function_org, repolist)
        ak = target_sat.api.ActivationKey(
            content_view=content_view, organization=function_org, environment=environment
        ).create()
        subscription = target_sat.api.Subscription(organization=function_org).search(
            query={'search': f'name={product.name}'}
        )[0]
        ak.add_subscriptions(data={'subscription_id': subscription.id})
        rhel_contenthost.install_katello_ca(target_sat)
        rhel_contenthost.register_contenthost(org=function_org.name, activation_key=ak.name)
        rhel_contenthost.add_rex_key(satellite=target_sat)
        rhel_contenthost.install_katello_host_tools()
        rhel_contenthost.execute('subscription-manager refresh')

        self._check_yum_plugins_count(rhel_contenthost)

        pkg_install = rhel_contenthost.execute(
            f'yum -y install {" ".join(constants.FAKE_9_YUM_OUTDATED_PACKAGES)}'
        )
        assert pkg_install.status == 0, 'Failed to install packages'
        host = target_sat.api.Host().search(query={'search': f'activation_key={ak.name}'})[0]
        assert host.id == rhel_contenthost.nailgun_host.id, 'Host not found in Satellite'
        assert (
            rhel_contenthost.applicable_errata_count > 1
        ), f'No applicable errata found for host {host.name}'
        erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)
        save_test_data(
            {
                'rhel_client': rhel_contenthost.hostname,
                'activation_key': ak.name,
                'custom_repo_id': custom_yum_repo.id,
                'product_id': product.id,
                'content_view_id': content_view.id,
                'synced_repo_ids': [repo.id for repo in synced_repos],
                'organization_id': function_org.id,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_generate_errata_for_client)
    def test_post_scenario_errata_count_installation(self, target_sat, pre_upgrade_data):
        """Post-upgrade scenario that applies errata on the RHEL client that was set up
        in the pre-upgrade test and verifies that the errata was applied correctly.

        :id: postupgrade-88fd28e6-b4df-46c0-91d6-784859fd1c21

        :steps:

            1. Recover pre_upgrade data for post_upgrade verification
            2. Verify errata count has not changed on Satellite
            4. Verify the errata_ids
            5. Verify installation of errata is successfull
            6. Verify that the errata application updated packages on client
            7. Verify that all expected erratas were installed on client.

        :expectedresults:
            1. errata count and erratum list should same after Satellite upgrade
            2. Installation of errata should pass successfully.

        :BZ: 1625649

        :customerscenario: true
        """
        client_hostname = pre_upgrade_data.get('rhel_client')
        custom_repo_id = pre_upgrade_data.get('custom_repo_id')
        activation_key = pre_upgrade_data.get('activation_key')
        organization_id = pre_upgrade_data.get('organization_id')
        rhel_client = Broker(host_class=ContentHost).from_inventory(
            filter=f'hostname={client_hostname}'
        )[0]
        custom_yum_repo = target_sat.api.Repository(id=custom_repo_id).read()
        host = target_sat.api.Host().search(query={'search': f'activation_key={activation_key}'})[0]
        assert host.id == rhel_client.nailgun_host.id, 'Host not found in Satellite'
        organization = target_sat.api.Organization(id=organization_id).read()

        self._check_yum_plugins_count(rhel_client)

        # Verifying errata count has not changed on Satellite
        installable_errata_count = rhel_client.applicable_errata_count
        assert installable_errata_count > 1, f'No applicable errata found for host {host.name}'
        erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)

        for errata in settings.repos.yum_9.errata:
            task_id = target_sat.api.JobInvocation().run(
                data={
                    'feature': 'katello_errata_install',
                    'inputs': {'errata': errata},
                    'targeting_type': 'static_query',
                    'search_query': f'name = {rhel_client.hostname}',
                    'organization_id': organization.id,
                },
            )['id']
            target_sat.wait_for_tasks(
                search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
                search_rate=15,
                max_tries=10,
            )
            installable_errata_count -= 1

        # waiting for errata count to become 0, as profile uploading take some amount of time
        wait_for(
            lambda: rhel_client.applicable_errata_count == 0,
            timeout=400,
            delay=2,
            logger=logger,
        )
        pkg_check = rhel_client.execute(f'rpm -q {" ".join(constants.FAKE_9_YUM_UPDATED_PACKAGES)}')
        assert pkg_check.status == 0, 'Package check failed. One or more packages were not updated'
        errata_check = rhel_client.execute('dnf updateinfo list')
        for errata in settings.repos.yum_9.errata:
            assert (
                errata not in errata_check.stdout
            ), 'Errata check failed. One or more errata were not applied'
