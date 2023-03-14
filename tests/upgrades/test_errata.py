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
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_9_YUM_OUTDATED_PACKAGES
from robottelo.constants import FAKE_9_YUM_UPDATED_PACKAGES
from robottelo.logging import logger


class TestScenarioErrataAbstract:
    """This is an Abstract Class whose methods are inherited by others errata
    scenarios"""

    def _create_custom_rhel_n_client_repos(self, target_sat, product, rhel_host):
        """Install packge on docker content host."""
        repos = []
        v_major = rhel_host.os_version.major
        rhel_repo_urls = [settings.repos[f'rhel{v_major}_os']]
        if v_major > 7:
            rhel_repo_urls = [rhel_repo_urls[0]['BASEOS'], rhel_repo_urls[0]['APPSTREAM']]

        client_repo_url = settings.repos.satclient_repo[f'rhel{v_major}']
        if all([all(rhel_repo_urls), client_repo_url]):
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

    def _get_rh_rhel_n_client_repos(self, target_sat, org, rhel_host):
        """Get list of RHEL (system) and Satellite Client repos

        :return: nailgun.entities.Repository: repository
        """
        rhel_repos = ['rhel_bos', 'rhel_aps'] if rhel_host.os_version.major > 7 else ['rhel']
        rhel_repo_ids = [
            target_sat.api.Repository(organization=org)
            .search(query={'search': rhel_host.REPOS[repo]['id']})[0]
            .id
            for repo in rhel_repos
        ]
        sat_client_repo_id = (
            target_sat.api.Repository(organization=org)
            .search(query={'search': rhel_host.REPOS[constants.PRODUCT_KEY_SAT_CLIENT]['id']})[0]
            .id
        )

        return [
            target_sat.api.Repository(id=repo_id)
            for repo_id in [*rhel_repo_ids, sat_client_repo_id]
        ]


class TestScenarioErrataCount(TestScenarioErrataAbstract):
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

    @pytest.mark.pre_upgrade
    def test_pre_scenario_generate_errata_for_client(
        self, katello_agent_client_for_upgrade, save_test_data
    ):
        """Create product and repo from which the errata will be generated for the
        Satellite client or content host.

        :id: preupgrade-88fd28e6-b4df-46c0-91d6-784859fd1c21

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
        sat = katello_agent_client_for_upgrade.sat
        rhel_client = katello_agent_client_for_upgrade.client
        org = sat.api.Organization().create()
        loc = sat.api.Location(organization=[org]).create()

        sat.update_vm_host_location(rhel_client, loc.id)
        environment = sat.api.LifecycleEnvironment(organization=org).search(
            query={'search': f'name={ENVIRONMENT}'}
        )[0]
        product = sat.api.Product(organization=org).create()
        custom_yum_repo = sat.api.Repository(
            product=product, content_type='yum', url=settings.repos.yum_9.url
        ).create()
        product.sync()
        synced_repos = self._create_custom_rhel_n_client_repos(sat, product, rhel_client)
        repolist = [
            custom_yum_repo,
            *synced_repos,
        ]
        content_view = sat.publish_content_view(org, repolist)
        ak = sat.api.ActivationKey(
            content_view=content_view, organization=org, environment=environment
        ).create()
        subscription = sat.api.Subscription(organization=org).search(
            query={'search': f'name={product.name}'}
        )[0]
        ak.add_subscriptions(data={'subscription_id': subscription.id})

        rhid = rhel_client.execute('subscription-manager identity')
        assert org.name in rhid.stdout

        rhel_client.execute(f'yum -y install {" ".join(FAKE_9_YUM_OUTDATED_PACKAGES)}')
        host = sat.api.Host().search(query={'search': f'activation_key={ak.name}'})[0]
        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        assert installable_errata_count > 1
        erratum_list = sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)
        save_test_data(
            {
                'rhel_client': rhel_client.hostname,
                'activation_key': ak.name,
                'custom_repo_id': custom_yum_repo.id,
                'product_id': product.id,
                'content_view_id': content_view.id,
                'synced_repo_ids': [repo.id for repo in synced_repos],
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_generate_errata_for_client)
    def test_post_scenario_errata_count_installation(self, target_sat, pre_upgrade_data):
        """Post-upgrade scenario that installs the package on pre-upgrade
        client remotely and then verifies if the package installed.

        :id: postupgrade-88fd28e6-b4df-46c0-91d6-784859fd1c21

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
        client_hostname = pre_upgrade_data.get('rhel_client')
        custom_repo_id = pre_upgrade_data.get('custom_repo_id')
        product_id = pre_upgrade_data.get('product_id')
        content_view_id = pre_upgrade_data.get('content_view_id')
        activation_key = pre_upgrade_data.get('activation_key')
        synced_repo_ids = pre_upgrade_data.get('synced_repo_ids')

        rhel_client = Broker().from_inventory(filter=f'hostname={client_hostname}')[0]
        product = target_sat.api.Product(id=product_id).read()
        content_view = target_sat.api.ContentView(id=content_view_id).read()
        custom_yum_repo = target_sat.api.Repository(id=custom_repo_id).read()
        synced_repos = [target_sat.api.Repository(id=id).read() for id in synced_repo_ids]

        product.sync(timeout=1400)
        for repo in synced_repos:
            content_view.repository.append(repo)
        content_view = content_view.update(['repository'])
        content_view.publish()

        host = target_sat.api.Host().search(query={'search': f'activation_key={activation_key}'})[0]
        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        assert installable_errata_count > 1

        erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)

        for errata in settings.repos.yum_9.errata:
            host.errata_apply(data={'errata_ids': [errata]})
            installable_errata_count -= 1

        # waiting for errata count to become 0, as profile uploading take some
        # amount of time
        wait_for(
            lambda: host.read().content_facet_attributes['errata_counts']['total'] == 0,
            timeout=400,
            delay=2,
            logger=logger,
        )
        rhel_client.execute(
            f'yum -y install {" ".join(FAKE_9_YUM_UPDATED_PACKAGES)}'
        )  # why do we install packages at the end of the test?


class TestScenarioErrataCountWithPreviousVersionKatelloAgent(TestScenarioErrataAbstract):
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

    @pytest.mark.pre_upgrade
    def test_pre_scenario_generate_errata_with_previous_version_katello_agent_client(
        self, katello_agent_client_for_upgrade, default_org, save_test_data
    ):
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
        sat = katello_agent_client_for_upgrade.sat
        rhel_client = katello_agent_client_for_upgrade.client
        environment = sat.api.LifecycleEnvironment(organization=default_org).search(
            query={'search': f'name={ENVIRONMENT}'}
        )[0]

        product = sat.api.Product(organization=default_org).create()
        custom_yum_repo = sat.api.Repository(
            product=product, content_type='yum', url=settings.repos.yum_9.url
        ).create()
        product.sync(timeout=1400)

        repos = [*self._get_rh_rhel_n_client_repos(default_org), custom_yum_repo]
        content_view = sat.publish_content_view(default_org, repos)
        custom_sub = sat.api.Subscription(organization=default_org).search(
            query={'search': f'name={product.name}'}
        )[0]
        rh_sub = sat.api.Subscription(organization=default_org).search(
            query={'search': f'{DEFAULT_SUBSCRIPTION_NAME}'}
        )[0]

        ak = sat.api.ActivationKey(
            content_view=content_view,
            organization=default_org,
            environment=environment,
            auto_attach=False,
        ).create()
        ak.add_subscriptions(data={'subscription_id': custom_sub.id})
        ak.add_subscriptions(data={'subscription_id': rh_sub.id})

        # Is this needed? The client should already be registered from the fixture
        wait_for(
            lambda: default_org.label
            in rhel_client.execute('subscription-manager identity').stdout,
            timeout=800,
            delay=2,
            logger=logger,
        )

        # Update OS to make errata count 0
        rhel_client.execute('yum -y update')

        rhel_client.execute(f'yum -y install {" ".join(FAKE_9_YUM_OUTDATED_PACKAGES)}')
        host = sat.api.Host().search(query={'search': f'activation_key={ak.name}'})[0]
        # TODO: check that the above host is the same as rhel_client.nailgun_host

        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        assert installable_errata_count > 1

        erratum_list = sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)
        save_test_data(
            {
                'rhel_client_hostname': rhel_client.hostname,
                'activation_key': ak.name,
                'custom_repo_id': custom_yum_repo.id,
            }
        )

    @pytest.mark.post_upgrade(
        depend_on=test_pre_scenario_generate_errata_with_previous_version_katello_agent_client
    )
    def test_post_scenario_generate_errata_with_previous_version_katello_agent_client(
        self, target_sat, pre_upgrade_data
    ):
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

        client_hostname = pre_upgrade_data.get('rhel_client_hostname')
        custom_repo_id = pre_upgrade_data.get('custom_repo_id')
        activation_key = pre_upgrade_data.get('activation_key')

        rhel_client = Broker().from_inventory(filter=f'hostname={client_hostname}')[0]
        custom_yum_repo = target_sat.api.Repository(id=custom_repo_id).read()
        host = (
            target_sat.api.Host()
            .search(query={'search': f'activation_key={activation_key}'})[0]
            .read()
        )

        installable_errata_count = host.content_facet_attributes['errata_counts']['total']
        assert installable_errata_count > 1
        erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)

        for errata in settings.repos.yum_9.errata:
            host.errata_apply(data={'errata_ids': [errata]})

        rhel_client.execute(f'yum -y install {" ".join(FAKE_9_YUM_UPDATED_PACKAGES)}')
        # Do we need to install the packages on the client?
        # The yum_9.errata(s) should already be installed

        # waiting for errata count to become 0, as profile uploading takes some time
        wait_for(
            lambda: host.read().content_facet_attributes['errata_counts']['total'] == 0,
            timeout=400,
            delay=2,
            logger=logger,
        )
