"""Test for Performance Tuning related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Installer

:Team: Platform

:CaseImportance: High

"""
import filecmp

import pytest

from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand


class TestScenarioPerformanceTuning:
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    Performance Tuning utility

    Test Steps::

        1. Before satellite upgrade.
           - Apply non-default tuning size using satellite-installer.
           - Check the tuning status and their set tuning parameters after applying the new size.
        2. Upgrade the satellite.
        3. Verify the following points.
              Before Upgrade:
                 - Satellite-installer work correctly with selected tune size.
                 - tune parameter set correctly on the satellite server.
              After Upgrade:
                 - Custom-hiera file should be unchanged.
                 - tune parameter should be unchanged.
                 - satellite-installer restore the default tune size.

    :expectedresults: Set tuning parameters and custom-hiera.yaml file should be unchanged after
    upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_pre_performance_tuning_apply(self, target_sat):
        """In preupgrade scenario we apply non-default tuning size.

        :id: preupgrade-83404326-20b7-11ea-a370-48f17f1fc2e1

        :steps:
            1. collect the custom_hira.yaml file before upgrade.
            2. Update the tuning size to non-default.
            3. Check the updated tuning size.
            4. If something gets wrong with updated tune size then restore the default tune size.

        :expectedresults: Non-default tuning parameter should be applied.

        """
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

    @pytest.mark.post_upgrade(depend_on=test_pre_performance_tuning_apply)
    def test_post_performance_tuning_apply(self, target_sat):
        """In postupgrade scenario, we verify the set tuning parameters and custom-hiera.yaml
        file's content.

        :id: postupgrade-31e26b08-2157-11ea-9223-001a4a1601d8

        :steps:
            1. Check the tuning size.
            2. Compare the custom-hiera.yaml file.
            3. Change the tuning size from non-default to default.

        :expectedresults:
            1. non-default tuning parameter should be set after upgrade.
            2. custom-hiera.yaml file should be unchanged after upgrade.
            3. tuning parameter update should work after upgrade.

        """
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
