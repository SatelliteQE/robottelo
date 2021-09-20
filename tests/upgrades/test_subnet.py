"""Test for Subnet related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: Networking

:Assignee: rdrazny

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
class TestPositiveCreateParamInExistingSubnet:
    """Parameters can be created in existing subnet post upgrade

    :id: 319317d5-70f0-40f3-bc33-d8846432dea2

    :steps:

        1. Create subnet with all the details preupgrade
            satellite version
        2. Create host with this subnet
        3. Upgrade Satellite
        4. Go to the subnet created in preupgrade satellite version
        5. Attempt to add parameter in subnet

    :expectedresults:

        1. The subnet should be created successfully.
        2. Parameter should be created in existing Subnet post
            upgrade
        3. Host ENC should return parameter with its value
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_parameter_in_existing_subnet(self):
        """Create parameter in preupgrade version"""

    @pytest.mark.post_upgrade
    def test_post_create_parameter_in_existing_subnet(self):
        """Parameter can be added to existing subnet post upgrade"""
