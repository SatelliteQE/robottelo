"""Test for Role related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: NotAutomated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities


@pytest.mark.stubbed
class TestFilterBecomesOverriddenFilterPostUpgrade:
    """Filter associated with taxonomies becomes overridden filter post upgrade

    :id: e8ecf446-375e-45fa-8e2c-558a40a7d8d0

    :steps:

        1. In Preupgrade Satellite, Create a role
        2. Add filter in a role to which taxonomies can be assigned
        3. Assign taxonomies to above filter
        4. Upgrade the satellite
        5. Postupgrade, View the above role filter

    :expectedresults:

        1. The role with taxonomies associated to them should be created
        2. The Filter should have set override flag postupgrade
        3. The locations and organizations of filter should be unchanged postupgrade
    """

    @pytest.mark.pre_upgrade
    def test_pre_existing_overriden_filter(self):
        """Role with taxonomies associated filter can be created"""

    @pytest.mark.post_upgrade
    def test_post_existing_overriden_filter(self):
        """Filter associated with taxonomies becomes overridden filter post upgrade"""


@pytest.mark.stubbed
class TestBuiltInRolesLockedPostUpgrade:
    """Builtin roles in satellite gets locked post upgrade

    :id: a856ca29-cb0d-4707-9b3b-90be822dd386

    :steps:

        1. Upgrade the satellite
        2. Post upgrade, attempt to clone the built in roles

    :expectedresults:

        1. Builtin roles of satellite should be locked and non-editable
        2. Built in roles of satellite should be allowed to clone
    """

    @pytest.mark.post_upgrade
    def test_post_builtin_roles_are_cloned(self):
        """Builtin roles in satellite gets locked post upgrade"""


@pytest.mark.stubbed
class TestNewOrganizationAdminRole:
    """New Organization Admin role creates post upgrade

    :id: 5765b8e2-5810-4cb7-86ac-a93f36de1dd9

    :steps:

        1. Upgrade the satellite
        2. Post upgrade, Attempt to clone organization admin role
        3. Assign taxonomies to cloned role

    :expectedresults:

        1. Post upgrade, new Organization Admin role should be created
        2. Organization Admin role should have filters by default
        3. Organization Admin role of satellite should be locked and
            non-editable
        4. Organization Admin role of satellite should be allowed to clone
        5. Taxonomies should be assigned to cloned org admin role
    """

    @pytest.mark.post_upgrade
    def test_post_builtin_roles_are_cloned(self):
        """New Organization Admin role creates post upgrade"""


class TestRoleAddPermission:
    """Default role extra added permission should be intact post upgrade

    :id: 3a350e4a-96b3-4033-b562-3130fc43a4bc

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding
            new permission
        2. Upgrade the satellite
        3. Postupgrade, Verify the permission in existing 'Default role' intact

    :expectedresults:

        1. Permission is added to existing 'Default role'.
        2. Post upgrade, The added permission in existing 'Default role' is intact
        post upgrade
    """

    @pytest.mark.pre_upgrade
    def test_pre_default_role_added_permission(self):
        """New permission is added to Default Role"""
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        subnetfilter = entities.Filter(
            permission=entities.Permission().search(
                filters={'name': 'view_subnets'}, query={'search': 'resource_type="Subnet"'}
            ),
            role=defaultrole,
        ).create()
        assert subnetfilter.id in [filt.id for filt in defaultrole.read().filters]

    @pytest.mark.post_upgrade(depend_on=test_pre_default_role_added_permission)
    def test_post_default_role_added_permission(self):
        """The new permission in 'Default role' is intact post upgrade"""
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
        2. Upgrade the satellite
        3. Postupgrade, Verify the permission with filter in existing
            'Default role' is intact

    :expectedresults:

        1. The new permissions added to the default role.
        2. Post upgrade, The added permission with filter in existing 'Default role'
            is intact post upgrade
    """

    @pytest.mark.pre_upgrade
    def test_pre_default_role_added_permission_with_filter(self):
        """New permission with filter is added to Default Role"""
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

    @pytest.mark.post_upgrade(depend_on=test_pre_default_role_added_permission_with_filter)
    def test_post_default_role_added_permission_with_filter(self):
        """The new permission with filter in 'Default role' is intact post upgrade"""
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        domainfilt = entities.Filter().search(
            query={'search': f'role_id={defaultrole.id} and permission="view_domains"'}
        )
        assert domainfilt
        assert domainfilt[0].search == 'name ~ a'
        # Teardown
        domainfilt[0].delete()
