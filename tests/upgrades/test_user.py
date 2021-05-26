"""Test for User related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade


class TestScenarioPositiveCreateSSHKeyInExistingUsers:
    """SSH Key can be created in existing user post upgrade

    :id: e4338daa-272a-42e3-be45-77e1caea607f

    :steps:

        1. From SuperAdmin create user with all the details preupgrade
            satellite version
        2. Upgrade Satellite to next/latest version
        3. Go to the user created in preupgrade satellite version
        4. Attempt to add SSH key in user

    :expectedresults: Satellite admin should be able to add SSH key in
        existing user post upgrade
    """

    @pre_upgrade
    def test_pre_create_sshkey_in_existing_user(self):
        """Create User in preupgrade version

        :steps: From SuperAdmin create user with all the details preupgrade
            satellite version

        :expectedresults: The user should be created successfully
        """

    @post_upgrade
    def test_post_create_sshkey_in_existing_user(self):
        """SSH key can be added to existing user post upgrade

        :steps: Postupgrade, Add SSH key to the existing user

        :expectedresults: SSH Key should be added to the existing user
        """


class TestScenarioPositiveExistingUserPasswordlessAccessToHost:
    """Existing user can password-less access to provisioned host

    :id: d2d94447-5fc7-49cc-840e-06568d8a5141

    :steps:

        1. In preupgrade satellite, From SuperAdmin create user with all the
            details
        2. Upgrade Satellite to next/latest satellite version
        3. Go to the user created in preupgrade satellite
        4. Add SSH key in that user
        5. Choose provisioning template you would use to provision the host
            in feature and add 'create_users' snippet in template
        6. Provision a host through the existing user
        7. Attempt to access the provisioned host through user

    :expectedresults: Existing User should be able to passwordless access to
        provisioned host
    """

    @pre_upgrade
    def test_pre_existing_user_passwordless_access_to_host(self):
        """Create User in preupgrade version

        :steps: In preupgrade satellite, From SuperAdmin create user with all
            the required details

        :expectedresults: The user should be created successfully
        """

    @post_upgrade
    def test_post_existing_user_passwordless_access_to_host(self):
        """Existing user can passwordless access to provisioned host

        :steps:

            1. Go to the user created in preupgrade satellite
            2. Add SSH key in that user
            3. Choose provisioning template you would use to provision the host
                in feature and add 'create_users' snippet in template
            4. Provision a host through the existing user
            5. Attempt to access the provisioned host through user

        :expectedresults: Existing User should be able to passwordless access
            to provisioned host
        """
