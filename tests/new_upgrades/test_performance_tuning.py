"""Test for Performance Tuning related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: High

"""

import filecmp

import pytest

from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def perf_tuning_upgrade_setup(perf_tuning_upgrade_shared_satellite, upgrade_action):
    """In preupgrade scenario we apply non-default tuning size.

    :steps:
        1. collect the custom_hira.yaml file before upgrade.
        2. Update the tuning size to non-default.
        3. Check the updated tuning size.
        4. If something gets wrong with updated tune size then restore the default tune size.

    :expectedresults: Non-default tuning parameter should be applied.

    """
    target_sat = perf_tuning_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        try:
            target_sat.get(
                local_path="custom-hiera-before-upgrade.yaml",
                remote_path="/etc/foreman-installer/custom-hiera.yaml",
            )
            installer_obj = InstallerCommand(tuning='development')
            command_output = target_sat.execute(installer_obj.get_command(), timeout='30m')
            assert 'Success!' in command_output.stdout
            installer_obj = InstallerCommand(help='tuning')
            command_output = target_sat.execute(installer_obj.get_command())
            assert 'default: "development"' in command_output.stdout

        except Exception as exp:
            logger.critical(exp)
            installer_obj = InstallerCommand(tuning='default')
            command_output = target_sat.execute(installer_obj.get_command(), timeout='30m')
            assert 'Success!' in command_output.stdout
            assert 'default: "default"' in command_output.stdout
            raise
        sat_upgrade.ready()
        target_sat._session = None
        yield target_sat


@pytest.mark.perf_tuning_upgrades
def test_post_performance_tuning_apply(perf_tuning_upgrade_setup):
    """In postupgrade scenario, we verify the set tuning parameters and custom-hiera.yaml
    file's content.

    :id: 31e26b08-2157-11ea-9223-001a4a1601d8

    :steps:
        1. Check the tuning size.
        2. Compare the custom-hiera.yaml file.
        3. Change the tuning size from non-default to default.

    :expectedresults:
        1. non-default tuning parameter should be set after upgrade.
        2. custom-hiera.yaml file should be unchanged after upgrade.
        3. tuning parameter update should work after upgrade.

    """
    target_sat = perf_tuning_upgrade_setup
    installer_obj = InstallerCommand(help='tuning')
    command_output = target_sat.execute(installer_obj.get_command(), timeout='30m')
    assert 'default: "development"' in command_output.stdout
    target_sat.get(
        local_path="custom-hiera-after-upgrade.yaml",
        remote_path="/etc/foreman-installer/custom-hiera.yaml",
    )
    assert filecmp.cmp('custom-hiera-before-upgrade.yaml', 'custom-hiera-after-upgrade.yaml')
    installer_obj = InstallerCommand(tuning='default')
    command_output = target_sat.execute(installer_obj.get_command(), timeout='30m')
    assert 'Success!' in command_output.stdout
    installer_obj = InstallerCommand(help='tuning')
    command_output = target_sat.execute(installer_obj.get_command())
    assert 'default: "default"' in command_output.stdout
