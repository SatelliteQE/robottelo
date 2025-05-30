"""Test for Remote Execution related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Puppet

:Team: Rocket

:CaseImportance: Medium

"""

from box import Box
import pytest

from robottelo.config import settings
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def puppet_upgrade_setup(puppet_upgrade_integrated_sat_cap, upgrade_action):
    satellite = puppet_upgrade_integrated_sat_cap.satellite
    capsule = puppet_upgrade_integrated_sat_cap.capsule
    with (
        SharedResource(satellite.hostname, upgrade_action, target_sat=satellite) as sat_upgrade,
        SharedResource(capsule.hostname, upgrade_action, target_sat=capsule) as cap_upgrade,
    ):
        test_data = Box(
            {
                'satellite': satellite,
                'capsule': capsule,
            }
        )
        sat_upgrade.ready()
        satellite._swap_nailgun(f'{settings.UPGRADE.TO_VERSION}.z')
        cap_upgrade.ready()
        satellite._session = None
        capsule._session = None
        yield test_data


@pytest.mark.puppet_upgrades
def test_post_puppet_active(puppet_upgrade_setup):
    """Test that puppet remains active after the upgrade on both,
    Satellite and Capsule.

    :id: postupgrade-6360e928-ba0f-41a7-9aaa-bea87cb6342d

    :steps:
        1. Check for capsule features.
        2. Check for puppetserver status.

    :expectedresults:
        1. Puppet and Puppetca features are enabled.
        2. Puppetserver is installed and runnning.

    :parametrized: yes

    """
    satellite = puppet_upgrade_setup.satellite
    capsule = puppet_upgrade_setup.capsule
    for server in satellite, capsule:
        result = server.get_features()
        assert 'puppet' in result
        assert 'puppetca' in result

        assert server.execute('rpm -q puppetserver').status == 0

        result = server.execute('systemctl status puppetserver')
        assert 'active (running)' in result.stdout


@pytest.mark.puppet_upgrades
def test_post_puppet_reporting(puppet_upgrade_setup):
    """Test that puppet is reporting to Satellite after the upgrade.

    :id:   postupgrade-cdc4f6cc-23d8-4b4a-bd94-5c86b3072828

    :steps:
        1. Run puppet agent on the registered Capsule.
        2. On Satellite, read puppet-originated Config reports for the Capsule host.

    :expectedresults:
        1. Puppet agent run succeeds.
        2. At least one Config report exists (was created) for the Capsule.

    """
    satellite = puppet_upgrade_setup.satellite
    capsule = puppet_upgrade_setup.capsule
    assert capsule.execute('puppet agent -t').status == 0

    result = satellite.cli.ConfigReport.list({'search': f'host={capsule.hostname},origin=Puppet'})
    assert len(result)
