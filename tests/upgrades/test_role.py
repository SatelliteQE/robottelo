"""Test for Role related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from upgrade_tests import pre_upgrade, post_upgrade


class scenario_positive_existing_overridden_filter:
    """Filter associated with taxonomies becomes overridden filter post upgrade

    :id: e8ecf446-375e-45fa-8e2c-558a40a7d8d0

    :steps:

        1. In Preupgrade Satellite, Create a role
        2. Add filter in a role to which taxonomies can be assigned
        3. Assign taxonomies to above filter
        4. Upgrade the satellite to next/latest version
        5. Postupgrade, View the above role filter

    :expectedresults:

        1. The Filter should be have set override flag postupgrade
        2. The locations and organizations of filter should be unchanged
            postupgrade
    """

    @pre_upgrade
    def test_pre_existing_overriden_filter(self):
        """Role with taxonomies associated filter can be created

        :steps:

            1. In Preupgrade Satellite, Create a role
            2. Add filter in a role to which taxonomies can be assigned
            3. Assign taxonomies to above filter

        :expectedresults: The role with taxonomies associated to them should
            be created
        """

    @post_upgrade
    def test_post_existing_overriden_filter(self):
        """Filter associated with taxonomies becomes overridden filter post
        upgrade

        :steps:

            1. Postupgrade, view the role filter created in preupgraded
                satellite

        :expectedresults:

            1. The Filter should be have set override flag postupgrade
            2. The locations and organizations of filter should be unchanged
                postupgrade
        """


class scenario_positive_builtin_roles_locked:
    """Builtin roles in satellite gets locked post upgrade

    :id: a856ca29-cb0d-4707-9b3b-90be822dd386

    :steps:

        1. Upgrade the satellite to next/latest version
        2. Post upgrade, attempt to clone the built in roles

    :expectedresults:

        1. Builtin roles of satellite should be locked and non-editable
        2. Built in roles of satellite should be allowed to clone
    """

    @post_upgrade
    def test_post_builtin_roles_are_cloned(self):
        """Builtin roles in satellite gets locked post upgrade

        :steps: Attempt to clone the built in roles post upgrade

        :expectedresults:

            1. Builtin roles of satellite should be locked and non-editable
            2. Built in roles of satellite should be allowed to clone
        """


class scenario_positive_new_organization_admin_role:
    """New Organization Admin role creates post upgrade

    :id: 5765b8e2-5810-4cb7-86ac-a93f36de1dd9

    :steps:

        1. Upgrade the satellite to next/latest version
        2. Post upgrade, Attmpt to clone organization admin role
        3. Assign taxonomies to cloned role

    :expectedresults:

        1. Post upgrade, new Organization Admin role should be created
        2. Organization Admin role should have filters by default
        3. Organization Admin role of satellite should be locked and
            non-editable
        4. Organization Admin role of satellite should be allowed to clone
        5. Taxonomies should be assigned to cloned org admin role
    """

    @post_upgrade
    def test_post_builtin_roles_are_cloned(self):
        """New Organization Admin role creates post upgrade

        :steps:

            1. Post upgrade, Attmpt to clone organization admin role
            2. Assign taxonomies to cloned role

        :expectedresults:

            1. Post upgrade, new Organization Admin role should be created
            2. Organization Admin role should have filters by default
            3. Organization Admin role of satellite should be locked and
                non-editable
            4. Organization Admin role of satellite should be allowed to clone
            5. Taxonomies should be assigned to cloned org admin role
        """
