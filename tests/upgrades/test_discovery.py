"""Test Discovery Plugin related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: DiscoveryImage

:Team: Rocket

:CaseImportance: High

"""

import re

from packaging.version import Version
import pytest


class TestDiscoveryImage:
    """Pre-upgrade and post-upgrade scenarios to test Foreman Discovery Image version.

    Test Steps:
        1. Before Satellite upgrade, Check the FDI version on the Satellite
        2. Upgrade satellite.
        3. Check the FDI version on the Satellite after upgrade to make sure its same or greater.
    """

    @pytest.mark.pre_upgrade
    def test_pre_upgrade_fdi_version(self, target_sat, save_test_data, request):
        """Test FDI version before upgrade.

        :id: preupgrade-8c94841c-6791-4af0-aa9c-e54c8d8b9a92

        :steps:
            1. Check installed version of FDI

        :expectedresults: Version should be saved and checked post-upgrade
        """
        target_sat.register_to_cdn()
        target_sat.execute('foreman-maintain packages install -y foreman-discovery-image')
        fdi_package = target_sat.execute('rpm -qa *foreman-discovery-image*').stdout
        # Note: The regular exp takes care of format digit.digit.digit or digit.digit.digit-digit in the output
        pre_upgrade_version = Version(re.search(r'\d+\.\d+\.\d+(-\d+)?', fdi_package).group())
        save_test_data({'pre_upgrade_version': pre_upgrade_version})

    @pytest.mark.post_upgrade(depend_on=test_pre_upgrade_fdi_version)
    def test_post_upgrade_fdi_version(self, target_sat, pre_upgrade_data):
        """Test FDI version post upgrade.

        :id: postugrade-38bdecaa-2b50-434b-90b1-4aa2b600d04e

        :steps:
            1. Check installed version of FDI

        :expectedresults: Version should be greater than or equal to pre_upgrade version
        """
        pre_upgrade_version = pre_upgrade_data.get('pre_upgrade_version')
        fdi_package = target_sat.execute('rpm -qa *foreman-discovery-image*').stdout
        # Note: The regular exp takes care of format digit.digit.digit or digit.digit.digit-digit in the output
        post_upgrade_version = Version(re.search(r'\d+\.\d+\.\d+(-\d+)?', fdi_package).group())
        assert post_upgrade_version >= pre_upgrade_version
        target_sat.unregister()
