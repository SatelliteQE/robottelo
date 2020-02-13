"""Test for Subnet related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade


class scenario_positive_create_parameters_in_existing_subnet:
    """Parameters can be created in existing subnet post upgrade

    :id: 319317d5-70f0-40f3-bc33-d8846432dea2

    :steps:

        1. Create subnet with all the details preupgrade
            satellite version
        2. Create host with this subnet
        2. Upgrade Satellite to next/latest satellite version
        3. Go to the subnet created in preupgrade satellite version
        4. Attempt to add parameter in subnet

    :expectedresults:

        1. Parameter should be created in existing Subnet post
            upgrade
        2. Host ENC should return parameter with its value
    """

    @pre_upgrade
    def test_pre_create_parameter_in_existing_subnet(self):
        """Create parameter in preupgrade version

        :steps:

            1. Create subnet with all the details preupgrade
                satellite version
            2. Create host with this subnet

        :expectedresults: The subnet should be created successfully
        """

    @post_upgrade
    def test_post_create_parameter_in_existing_subnet(self):
        """Parameter can be added to existing subnet post upgrade

        :steps:

            1. Postupgrade, Add parameter to the existing subnet

        :expectedresults:

            1. Parameter should be added to the existing subnet
            2. Host ENC should return parameter with its value
        """
