"""Test Discovery Plugin related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: DiscoveryImage

:Team: Rocket

:CaseImportance: High

"""

import re

from box import Box
from packaging.version import Version
import pytest

from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def fdi_upgrade_setup(fdi_upgrade_shared_satellite, upgrade_action):
    """Perform setup for Foreman Discovery Image upgrade test.

    :id: preupgrade-8c94841c-6791-4af0-aa9c-e54c8d8b9a92

    :steps:
        1. Check installed version of FDI

    :expectedresults: Version should be saved and checked post-upgrade
    """
    target_sat = fdi_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        target_sat.register_to_cdn()
        target_sat.execute('foreman-maintain packages install -y foreman-discovery-image')
        fdi_package = target_sat.execute('rpm -qa *foreman-discovery-image*').stdout
        # Note: The regular exp takes care of format digit.digit.digit or digit.digit.digit-digit in the output
        pre_upgrade_version = Version(re.search(r'\d+\.\d+\.\d+(-\d+)?', fdi_package).group())
        test_data = Box(
            {
                'target_sat': target_sat,
                'pre_upgrade_version': str(pre_upgrade_version),
            }
        )
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.discovery_upgrades
def test_post_upgrade_fdi_version(fdi_upgrade_setup):
    """Test FDI version post upgrade.

    :id: postugrade-38bdecaa-2b50-434b-90b1-4aa2b600d04e

    :steps:
        1. Check installed version of FDI

    :expectedresults: Version should be greater than or equal to pre_upgrade version
    """
    pre_upgrade_version = fdi_upgrade_setup.pre_upgrade_version
    target_sat = fdi_upgrade_setup.target_sat
    fdi_package = target_sat.execute('rpm -qa *foreman-discovery-image*').stdout
    # Note: The regular exp takes care of format digit.digit.digit or digit.digit.digit-digit in the output
    post_upgrade_version = Version(re.search(r'\d+\.\d+\.\d+(-\d+)?', fdi_package).group())
    assert post_upgrade_version >= Version(pre_upgrade_version)
    target_sat.unregister()
