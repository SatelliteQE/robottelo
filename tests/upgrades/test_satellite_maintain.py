"""satellite-maintain Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: High

"""

import re

import pytest


class TestSatelliteMaintain:
    """Pre-upgrade and post-upgrade scenarios to test satellite-maintain utility.

    Test Steps:
        1. Before Satellite upgrade, Perform test for "satellite-maintain upgrade list-versions"
        2. Upgrade satellite/capsule.
        3. Perform tests for satellite-maintain upgrade list-versions, after upgrade.
        4. Check if tests passed.
    """

    @staticmethod
    def satellite_upgradable_version_list(sat_obj):
        """Obtain upgradable version list by satellite-maintain.

        :return: upgradeable_versions
        """
        cmd = 'satellite-maintain upgrade list-versions --disable-self-upgrade'
        list_versions = sat_obj.execute(cmd).stdout
        regex = re.compile(r'^\d+\.\d+')
        return [version for version in list_versions if regex.match(version)]

    @pytest.mark.pre_upgrade
    def test_pre_satellite_maintain_upgrade_list_versions(self, target_sat):
        """Test list of satellite target versions before upgrade.

        :id: preupgrade-fc2c54b2-2663-11ea-b47c-48f17f1fc2e1

        :steps:
            1. Run satellite-maintain upgrade list-versions

        :expectedresults: Versions should be current z-stream.
        """
        zstream = '.'.join(target_sat.version.split('.')[0:2]) + '.z'
        upgradable_versions = self.satellite_upgradable_version_list(target_sat)
        # only possible target should be appropriate zstream
        assert set(upgradable_versions) - {zstream} == set()

    @pytest.mark.post_upgrade
    def test_post_satellite_maintain_upgrade_list_versions(self, target_sat):
        """Test list of satellite target versions after upgrade.

        :id: postupgrade-0bce689c-2664-11ea-b47c-48f17f1fc2e1

        :steps:
            1. Run satellite-maintain upgrade list-versions.

        :expectedresults: Versions should be next z-stream.
        """
        zstream = '.'.join(target_sat.version.split('.')[0:2]) + '.z'
        upgradable_versions = self.satellite_upgradable_version_list(target_sat)
        # only possible target should be appropriate zstream
        assert set(upgradable_versions) - {zstream} == set()
