"""Test for Performance Tuning related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Performance

:Assignee: psuriset

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import filecmp

import pytest

from robottelo.helpers import InstallerCommand
from robottelo.logging import logger


class TestScenarioPerformanceTuning:
    """Test Performance Tuning utility post upgrade

    :id: 83404326-20b7-11ea-a370-48f17f1fc2e1

    :steps:

        1. Before satellite upgrade.
           - Apply the medium tune size using satellite-installer.
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
    def test_pre_performance_tuning_apply(self, default_sat):

        """In preupgrade scenario we apply the medium tuning size.

        :steps:

            1. Create the custom-hiera.yaml file based on mongodb type and selected tune size.
            2. Run the satellite-installer --disable-system-checks to apply the medium tune size.
            3. Check the satellite-installer command status
            4. Check the applied parameter's value, to make sure the values are set successfully
            or not.
            5. If something gets wrong with updated tune parameter restore the system states with
             default custom-hiera.yaml file.
        """
        try:
            default_sat.get(
                local_path="custom-hiera-before-upgrade.yaml",
                remote_path="/etc/foreman-installer/custom-hiera.yaml",
            )
            installer_obj = InstallerCommand(tuning='medium')
            command_output = default_sat.execute(installer_obj.get_command())
            assert 'Success!' in command_output.stdout
            installer_obj = InstallerCommand(help='tuning')
            command_output = default_sat.execute(installer_obj.get_command())
            assert 'default: "medium"' in command_output.stdout

        except Exception as exp:
            logger.critical(exp)
            installer_obj = InstallerCommand(tuning='default')
            command_output = default_sat.execute(installer_obj.get_command())
            assert 'Success!' in command_output.stdout
            assert 'default: "default"' in command_output.stdout
            raise

    @pytest.mark.post_upgrade(depend_on=test_pre_performance_tuning_apply)
    def test_post_performance_tuning_apply(self, default_sat):
        """In postupgrade scenario, we verify the set tuning parameters and custom-hiera.yaml
        file's content.

        :steps:

            1: Download the custom-hiera.yaml after upgrade from upgraded setup.
            2: Compare it with the medium tune custom-hiera file.
            3. Check the tune settings in scenario.yaml file, it should be set as
            "default" with updated medium tune parameters.
            4. Upload the default custom-hiera.yaml file on the upgrade setup.
            5. Run the satellite installer with "default" tune argument(satellite-installer
            --tuning default -s --disable-system-checks).
            6. If something gets wrong with the default tune parameters then we restore the
            default original tune parameter.
        """
        installer_obj = InstallerCommand(help='tuning')
        command_output = default_sat.execute(installer_obj.get_command())
        assert 'default: "medium"' in command_output.stdout
        default_sat.get(
            local_path="custom-hiera-after-upgrade.yaml",
            remote_path="/etc/foreman-installer/custom-hiera.yaml",
        )
        assert filecmp.cmp('custom-hiera-before-upgrade.yaml', 'custom-hiera-after-upgrade.yaml')
        installer_obj = InstallerCommand(tuning='default')
        command_output = default_sat.execute(installer_obj.get_command())
        assert 'Success!' in command_output.stdout
        installer_obj = InstallerCommand(help='tuning')
        command_output = default_sat.execute(installer_obj.get_command())
        assert 'default: "default"' in command_output.stdout
