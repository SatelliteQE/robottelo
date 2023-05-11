"""Test for Client related Upgrade Scenario's

content-host-d containers use SATHOST env var, which is passed through sat6-upgrade functions
sat6-upgrade requires env.satellite_hostname to be set, this is required for these tests

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:Team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import Broker

from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE_NAME
from robottelo.hosts import ContentHost


class TestScenarioUpgradeOldClientAndPackageInstallation:
    """This section contains pre and post upgrade scenarios to test if the
    package can be installed on the preupgrade client remotely.

    Test Steps::

        1. Before Satellite upgrade, create a content host and register it with
            Satellite
        2. Upgrade Satellite and client
        3. Install package post upgrade on a pre-upgrade client from Satellite
        4. Check if the package is installed on the pre-upgrade client
    """

    @pytest.mark.pre_upgrade
    def test_pre_scenario_pre_client_package_installation(
        self, katello_agent_client_for_upgrade, module_org, module_target_sat, save_test_data
    ):
        """Create product and repo, from which a package will be installed
        post upgrade. Create a content host and register it.

        :id: preupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :setup:

            1. Create and sync repo from which a package can be
                installed on content host
            2. Add repo to CV and then to Activation key


        :steps:

            1. Create a container as content host and register with Activation key

        :expectedresults:

            1. The "pre-upgrade" content host is created and registered.
            2. The new repo is enabled on the content host.

        """
        rhel_client = katello_agent_client_for_upgrade.client
        module_target_sat.cli.Host.package_install(
            {'host-id': rhel_client.nailgun_host.id, 'packages': FAKE_4_CUSTOM_PACKAGE_NAME}
        )
        result = rhel_client.execute(f"rpm -q {FAKE_4_CUSTOM_PACKAGE_NAME}")
        assert FAKE_4_CUSTOM_PACKAGE_NAME in result.stdout

        # Save client info to disk for post-upgrade test
        save_test_data(
            {
                'rhel_client': rhel_client.hostname,
                'org_id': module_org.id,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_pre_client_package_installation)
    def test_post_scenario_pre_client_package_installation(
        self, module_target_sat, pre_upgrade_data
    ):
        """Post-upgrade install of a package on a client created and registered pre-upgrade.

        :id: postupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :steps: Install package on the pre-upgrade registered client

        :expectedresults: The package is installed on client
        """
        client_name = pre_upgrade_data.get('rhel_client')
        client_id = (
            module_target_sat.api.Host().search(query={'search': f'name={client_name}'})[0].id
        )
        module_target_sat.cli.Host.package_install(
            {'host-id': client_id, 'packages': FAKE_0_CUSTOM_PACKAGE_NAME}
        )
        # Verifies that package is really installed
        rhel_client = Broker(host_class=ContentHost).from_inventory(
            filter=f'@inv.hostname == "{client_name}"'
        )[0]
        result = rhel_client.execute(f"rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}")
        assert FAKE_0_CUSTOM_PACKAGE_NAME in result.stdout


class TestScenarioUpgradeNewClientAndPackageInstallation:
    """This section contains post-upgrade scenarios to test if a package
    can be installed on a client created postupgrade, remotely.

    Test Steps:

        1. Upgrade Satellite
        2. After Satellite upgrade, create a content host and register it with
            Satellite
        3. Install package to the client from Satellite
        4. Check if the package is installed on the post-upgrade client
    """

    @pytest.mark.post_upgrade
    def test_post_scenario_post_client_package_installation(
        self,
        module_target_sat,
        katello_agent_client_for_upgrade,
    ):
        """Post-upgrade test that creates a client, installs a package on
        the post-upgrade created client and then verifies the package is installed.

        :id: postupgrade-1a881c07-595f-425f-aca9-df2337824a8e

        :steps:

            1. Create a content host with existing client ak
            2. Create and sync new post-upgrade repo from which a package will be
                installed on content host
            3. Add repo to CV and then in Activation key
            4. Install package on the pre-upgrade client

        :expectedresults:

            1. The content host is created
            2. The new repo and its product has been added to ak using which
                the content host is created
            3. The package is installed on post-upgrade client
        """
        rhel_client = katello_agent_client_for_upgrade.client
        module_target_sat.cli.Host.package_install(
            {'host-id': rhel_client.nailgun_host.id, 'packages': FAKE_0_CUSTOM_PACKAGE_NAME}
        )
        # Verifies that package is really installed
        result = rhel_client.execute(f"rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}")
        assert FAKE_0_CUSTOM_PACKAGE_NAME in result.stdout
