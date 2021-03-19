"""Test for Role related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade


@pytest.mark.stubbed
class TestOverriddenFilter:
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


@pytest.mark.stubbed
class TestBuiltInRolesLocked:
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


@pytest.mark.stubbed
class TestNewOrganizationAdminRole:
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


class TestRoleAddPermission:
    """Default role extra added permission should be intact post upgrade

    :id: 3a350e4a-96b3-4033-b562-3130fc43a4bc

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding
            new permission
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the permission in existing 'Default role' intact

    :expectedresults: The added permission in existing 'Default role' is intact
        post upgrade
    """

    @pre_upgrade
    def test_pre_default_role_added_permission(self):
        """New permission is added to Default Role

        :steps: New permission is added to existing 'Default role'

        :expectedresults: Permission is added to existing 'Default role'.

        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        subnetfilter = entities.Filter(
            permission=entities.Permission().search(
                filters={'name': 'view_subnets'}, query={'search': 'resource_type="Subnet"'}
            ),
            role=defaultrole,
        ).create()
        assert subnetfilter.id in [filt.id for filt in defaultrole.read().filters]

    @post_upgrade(depend_on=test_pre_default_role_added_permission)
    def test_post_default_role_added_permission(self):
        """The new permission in 'Default role' is intact post upgrade

        :expectedresults: The added permission in existing 'Default role' is
            intact post upgrade
        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        subnetfilt = entities.Filter().search(
            query={'search': f'role_id={defaultrole.id} and permission="view_subnets"'}
        )
        assert subnetfilt
        # Teardown
        subnetfilt[0].delete()


class TestRoleAddPermissionWithFilter:
    """Default role extra added permission with filter should be intact post
        upgrade

    :id: b287b71c-42fd-4612-a67a-b93d47dbbb33

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding
            new permission with filter
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the permission with filter in existing
            'Default role' is intact

    :expectedresults: The added permission with filter in existing
        'Default role' is intact post upgrade
    """

    @pre_upgrade
    def test_pre_default_role_added_permission_with_filter(self):
        """New permission with filter is added to Default Role

        :steps: New permission is added to existing 'Default role' with filter

        :expectedresults: Permission with filter is added to existing
            'Default role'

        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        domainfilter = entities.Filter(
            permission=entities.Permission().search(
                filters={'name': 'view_domains'}, query={'search': 'resource_type="Domain"'}
            ),
            unlimited=False,
            role=defaultrole,
            search='name ~ a',
        ).create()
        assert domainfilter.id in [filt.id for filt in defaultrole.read().filters]

    @post_upgrade(depend_on=test_pre_default_role_added_permission_with_filter)
    def test_post_default_role_added_permission_with_filter(self):
        """The new permission with filter in 'Default role' is intact post
            upgrade

        :expectedresults: The added permission with filter in existing
            'Default role' is intact post upgrade
        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        domainfilt = entities.Filter().search(
            query={'search': f'role_id={defaultrole.id} and permission="view_domains"'}
        )
        assert domainfilt
        assert domainfilt[0].search == 'name ~ a'
        # Teardown
        domainfilt[0].delete()
