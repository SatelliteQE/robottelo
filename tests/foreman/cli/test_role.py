# -*- encoding: utf-8 -*-
"""Test for Roles CLI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from math import ceil
from random import choice

from fauxfactory import gen_string

from robottelo.cli.base import CLIDataBaseError
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.filter import Filter
from robottelo.cli.role import Role
from robottelo.cli.settings import Settings
from robottelo.cli.user import User
from robottelo.constants import PERMISSIONS
from robottelo.constants import ROLES
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class RoleTestCase(CLITestCase):
    """Test class for Roles CLI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create new roles with provided name

        :id: 6883177c-6926-428c-92ab-9effbe1372ae

        :expectedresults: Role is created and has correct name

        :BZ: 1138553

        :CaseImportance: Critical
        """
        for name in generate_strings_list(length=10):
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)

    @tier1
    def test_positive_create_with_filter(self):
        """Create new role with a filter

        :id: 6c99ee25-4e58-496c-af42-f8ad2da6cf07

        :expectedresults: Role is created and correct filter is assigned

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions(
                {'resource-type': 'Organization'})
            ]
        # Assign filter to created role
        filter_ = make_filter({
            'role-id': role['id'],
            'permissions': permissions,
        })
        self.assertEqual(role['name'], filter_['role'])

    @tier1
    @upgrade
    def test_positive_create_with_permission(self):
        """Create new role with a set of permission

        :id: 7cb2b2e2-ad4d-41e9-b6b2-c0366eb09b9a

        :expectedresults: Role is created and has correct set of permissions

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions(
                {'resource-type': 'Organization'})
            ]
        # Assign filter to created role
        make_filter({
            'role-id': role['id'],
            'permissions': permissions,
        })
        self.assertEqual(
            set(Role.filters({'id': role['id']})[0]['permissions']),
            set(permissions)
        )

    @tier1
    def test_positive_delete_by_id(self):
        """Create a new role and then delete role by its ID

        :id: 351780b4-697c-4f87-b989-dd9a9a2ad012

        :expectedresults: Role is created and then deleted by its ID

        :CaseImportance: Critical
        """
        for name in generate_strings_list(length=10):
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)
                Role.delete({'id': role['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Role.info({'id': role['id']})

    @tier1
    def test_positive_update_name(self):
        """Create new role and update its name

        :id: 3ce1b337-fd52-4460-b8a8-df49c94ffed1

        :expectedresults: Role is created and its name is updated

        :CaseImportance: Critical
        """
        role = make_role({'name': gen_string('alpha', 15)})
        for new_name in generate_strings_list(length=10):
            with self.subTest(new_name):
                Role.update({
                    'id': role['id'],
                    'new-name': new_name,
                })
                role = Role.info({'id': role['id']})
                self.assertEqual(role['name'], new_name)

    @tier1
    def test_positive_list_filters_by_id(self):
        """Create new role with a filter and list it by role id

        :id: 6979ad8d-629b-481e-9d3a-8f3b3bca53f9

        :expectedresults: Filter is listed for specified role

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions(
                {'resource-type': 'Organization'})
            ]
        # Assign filter to created role
        filter_ = make_filter({
            'role-id': role['id'],
            'permissions': permissions,
        })
        self.assertEqual(role['name'], filter_['role'])
        self.assertEqual(
            Role.filters({'id': role['id']})[0]['id'], filter_['id'])

    @tier1
    def test_positive_list_filters_by_name(self):
        """Create new role with a filter and list it by role name

        :id: bbcb3982-f484-4dde-a3ea-7145fd28ab1f

        :expectedresults: Filter is listed for specified role

        :CaseImportance: Critical
        """
        role = make_role()
        # Pick permissions by its resource type
        permissions = [
            permission['name']
            for permission in Filter.available_permissions(
                {'resource-type': 'Organization'})
            ]
        # Assign filter to created role
        filter_ = make_filter({
            'role': role['name'],
            'permissions': permissions,
        })
        self.assertEqual(role['name'], filter_['role'])
        self.assertEqual(
            Role.filters({'name': role['name']})[0]['id'], filter_['id'])

    @tier1
    def test_negative_list_filters_without_parameters(self):
        """Try to list filter without specifying role id or name

        :id: 56cafbe0-d1cb-413e-8eac-0e01a3590fd2

        :expectedresults: Proper error message is shown instead of SQL error

        :CaseImportance: Critical

        :BZ: 1296782
        """
        with self.assertRaises(CLIReturnCodeError) as err:
            with self.assertNotRaises(CLIDataBaseError):
                Role.filters()
        self.assertRegex(
            err.exception.msg, 'At least one of options .* is required')

    @tier1
    @upgrade
    def test_positive_list_filters_with_pagination(self):
        """Make sure filters list can be displayed with different items per
        page value

        :id: b9c7c6c1-70c2-4d7f-8d36-fa8613acc865

        :BZ: 1428516

        :expectedresults: `per-page` correctly sets amount of items displayed
            per page, different `per-page` values divide a list into correct
            number of pages

        :CaseImportance: Critical
        """
        role = make_role()
        res_types = iter(PERMISSIONS.keys())
        permissions = []
        # Collect more than 20 different permissions
        while len(permissions) <= 20:
            permissions += [
                permission['name']
                for permission in Filter.available_permissions(
                    {'resource-type': next(res_types)})
            ]
        # Create a filter for each permission
        for perm in permissions:
            make_filter({
                'role': role['name'],
                'permissions': perm,
            })
        # Test different `per-page` values
        for per_page in (1, 5, 20):
            with self.subTest(per_page):
                # Verify the first page contains exactly the same items count
                # as `per-page` value
                filters = Role.filters({
                    'name': role['name'],
                    'per-page': per_page,
                })
                self.assertEqual(len(filters), per_page)
                # Verify pagination and total amount of pages by checking the
                # items count on the last page
                last_page = ceil(len(permissions) / per_page)
                filters = Role.filters({
                    'name': role['name'],
                    'page': last_page,
                    'per-page': per_page,
                })
                self.assertEqual(
                    len(filters), len(permissions) % per_page or per_page)

    @tier1
    @upgrade
    def test_positive_delete_cloned_builtin(self):
        """Clone a builtin role and attempt to delete it

        :id: 1fd9c636-596a-4cb2-b100-de19238042cc

        :BZ: 1426672

        :expectedresults: role was successfully deleted

        :CaseImportance: Critical

        """
        role_list = Role.list({
            'search': 'name=\\"{}\\"'.format(choice(ROLES))})
        self.assertEqual(len(role_list), 1)
        cloned_role = Role.clone({
            'id': role_list[0]['id'],
            'new-name': gen_string('alphanumeric'),
        })
        Role.delete({'id': cloned_role['id']})
        with self.assertRaises(CLIReturnCodeError):
            Role.info({'id': cloned_role['id']})


class CannedRoleTestCases(CLITestCase):
    """Implements Canned Roles tests from UI

    :CaseAutomation: notautomated
    """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_role_with_taxonomies(self):
        """create role with taxonomies

        :id: 4ce9fd35-4d3d-47f7-8bc6-7cf0b3b2d2f5

        :steps: Create new role with taxonomies

        :expectedresults: New role is created with taxonomies

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_role_without_taxonomies(self):
        """Create role without taxonomies

        :id: 4dc80114-9629-487f-805c-c14241bdcde1

        :steps: Create new role without any taxonomies

        :expectedresults: New role is created without taxonomies

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_filter_without_override(self):
        """Create filter in role w/o overriding it

        :id: 247ab670-29e6-4c14-9140-51966f4632f4

        :steps:

            1. Create a role with taxonomies assigned
            2. Create filter in role without overriding it

        :expectedresults:

            1. Filter w/o override is created in role
            2. The taxonomies of role are inherited to filter
            3. Override check is not marked by default in filters table

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_non_overridable_filter(self):
        """Create non overridable filter in role

        :id: c53713a3-d4b6-47a1-b19e-8d2020f98efd

        :steps:

            1. Create a filter to which taxonomies cannot be associated.
            e.g Architecture filter

        :expectedresults:

            1. Filter is created without taxonomies
            2. Filter doesnt inherit taxonomies from role

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_override_non_overridable_filter(self):
        """Override non overridable filter

        :id: 163313eb-4401-4bb0-bf9a-58030251643b

        :steps: Attempt to override a filter to which taxonomies cannot be
            associated.  e.g Architecture filter

        :expectedresults: Filter is not overrided as taxonomies cannot be
            applied to that filter

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_overridable_filter(self):
        """Create overridable filter in role

        :id: 47816636-d215-45a8-9d21-495b1e193913

        :steps:

            1. Create a filter to which taxonomies can be associated.
            e.g Domain filter
            2. Override a filter with some taxonomies

        :expectedresults:

            1. Filter is created with taxonomies
            2. Override check is set to true
            3. Filter doesnt inherits taxonomies from role

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_update_role_taxonomies(self):
        """Update role taxonomies which applies to its non-overrided filters

        :id: 988cf8c6-8f6e-49de-be54-d17085f260b6

        :steps:

            1. Create role with organization A and Location A
            2. Add filter in above role without overriding
            3. Update role set Organization to B and Location to B
            4. List roles overridden filter taxonomies

        :expectedresults: The taxonomies of filter should be updated with
            role taxonomies

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_role_taxonomies(self):
        """Update of role taxonomies doesnt applies on its overridden filters

        :id: 43ae1561-4362-47e4-b964-c5e2be791927

        :steps:

            1. Create role with organization A and Location A
            2. Add overridden filter in above role with Organization A and
                Location A
            3. Update role set Organization to B and Location to B
            4. List roles overridden filter taxonomies

        :expectedresults: The taxonomies of overridden filter should not be
            updated with role taxonomies
        """

    @stubbed()
    @tier2
    def test_positive_override_flag(self):
        """Overridden role filters flag

        :id: 08925cb0-856e-48a6-ba88-eda21c8d3619

        :steps:

            1. Create role with an overridden filter
            2. List above role filters

        :expectedresults: The override flag should be displayed for
            overridden filter in role filters table

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_disable_filter_override(self):
        """Unsetting override flag resets filter taxonomies

        :id: 985d87c1-3db7-40d1-9719-a7e7a85dce4d

        :steps:

            1. Create role organization A and Location A
            2. Create an overridden filter in role with organization B
                and Location B
            3. Unset filter override flag in role
            4. List above role filters

        :expectedresults: On unsetting filter override, the override flag
            should be set to false in role filters table

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_create_org_admin_from_clone(self):
        """Create Org Admin role which has access to most of the resources
        within organization

        :id: a173f00b-60eb-4cc2-9a10-1ab3a18563a0

        :steps:

            1. create Org Admin role by cloning 'Organization admin' role which
                has most resources permissions

        :expectedresults: Org Admin role should be created successfully
        """

    @stubbed()
    @tier1
    def test_positive_create_cloned_role_with_taxonomies(self):
        """Taxonomies can be assigned to cloned role

        :id: 56d29da5-27e0-4855-974c-e4fa50a1631b

        :steps:

            1. Create Org Admin role by cloning 'Organization admin' role
            2. Set new taxonomies (locations and organizations) to cloned role

        :expectedresults:

            1. While cloning, role allows to set taxonomies
            2. New taxonomies should be applied to cloned role successfully
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_access_entities_from_org_admin(self):
        """User can access resources within its taxonomies if assigned role
        has permission for same taxonomies

        :id: 555a4942-a4bb-499f-95a2-88e686518073

        :steps:

            1. Create Org Admin role and assign taxonomies to it
            2. Create user with same taxonomies as role above
            3. Assign cloned role to user above
            4. Attempt to access resources with user

        :expectedresults: User should be able to access all the resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_org_admin(self):
        """User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 2c0b6e8e-c8b7-4212-af79-d329bd803558

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user
            4. Attempt to access resources with user

        :expectedresults: User should not be able to access any resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_user(self):
        """User can not access resources within its own taxonomies if assigned
        role does not have permissions for user taxonomies

        :id: 512d2758-2ca0-49c2-b80e-f8a7bffd35b4

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user.
            4. Attempt to access resources with user

        :expectedresults: User should not be able to access any resources and
            permissions in his own taxonomies

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_override_cloned_role_filter(self):
        """Cloned role filter overrides

        :id: 0711541f-1af6-4493-b1f2-552367541d99

        :steps:

            1. Create a role with overridden filter
            2. Clone above role
            3. Attempt to override the filter in cloned role

        :expectedresults: Filter in cloned role should be overridden

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_emptiness_of_filter_taxonomies_on_role_clone(self):
        """Taxonomies of filters in cloned role are set to None for filters that
        are overridden in parent role

        :id: 20179b43-9db7-4af4-beca-fecc7ff7490c

        :steps:

            1. Create a role with an overridden filter
            2. Overridden filter should have taxonomies assigned
            3. Clone above role
            4. View cloned role filters

        :expectedresults:

            1. Taxonomies of the 'parent role overridden filters' are set to
                None in cloned role
            2. Override flag is set to True in filters table

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_override_empty_filter_taxonomies_in_cloned_role(self):
        """Taxonomies of filters in cloned role can be overridden for filters that
        are overridden in parent role

        :id: 7a12aba4-565e-4a17-8952-132158d1e0aa

        :steps:

            1. Create a role with an overridden filter
            2. Overridden filter should have taxonomies assigned
            3. In cloned role, override 'parent role overridden filters' by
                assigning some taxonomies to it

        :expectedresults: In cloned role, The taxonomies should be able to
            assign to 'parent role overridden filters'

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_overridden_filter_with_taxonomies(self):# noqa
        """When taxonomies assigned to cloned role, Unlimited and Override flag
        sets on filter that is overridden in parent role

        :id: 905f40ba-f6e7-45d3-a213-8deec9968374

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. List cloned role filter

        :expectedresults: Unlimited and Override flags should be set to True on
            filter that is overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_with_taxonomies_having_non_overridden_filter(self):# noqa
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter that is not overridden in parent role

        :id: 6985358c-c666-4cf5-b6c8-9030de8cf27c

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. List cloned role filter

        :expectedresults: Both unlimited and override flag should be set to
            False on filter that is not overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_unlimited_filter_with_taxonomies(self):
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter that is unlimited in parent role

        :id: 0774fca4-fa00-4067-8ac6-a77615b5651a

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Clone above role and assign Organization A and Location A
                while cloning
            4. List cloned role filter

        :expectedresults: Both unlimited and override flags should be set to
            False on filter that is unlimited in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_overridden_filter_without_taxonomies(self):# noqa
        """When taxonomies not assigned to cloned role, Unlimited and override
        flags sets on filter that is overridden in parent role

        :id: c792fc37-503d-4a85-8bd6-a5506e70dd3e

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Clone above role without assigning taxonomies
            4. List cloned role filter

        :expectedresults: Both unlimited and Override flags should be set to
            True on filter that is overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_without_taxonomies_non_overided_filter(self):
        """When taxonomies not assigned to cloned role, only unlimited but not
        override flag sets on filter that is overridden in parent role

        :id: 92264a5f-7cd8-4a91-8089-f2f546f556b3

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Clone above role without assigning taxonomies
            4. List cloned role filter

        :expectedresults:

            1. Unlimited flag should be set to True
            2. Override flag should be set to False

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_without_taxonomies_unlimited_filter(self):
        """When taxonomies not assigned to cloned role, Unlimited and override
        flags sets on filter that is unlimited in parent role

        :id: 2f205923-f590-4797-b63b-adf389f802e6

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Clone above role without assigning taxonomies
            4. List cloned role filter

        :expectedresults:

            1. Unlimited flag should be set to True
            2. Override flag should be set to False

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_force_unlimited(self):
        """Unlimited flag forced sets to filter when no taxonomies are set to role
        and filter

        :id: 2de03e36-7f8d-4b17-819a-0d3b4468e32c

        :steps:

            1. Create a role with organization A and Location A
            2. Create a role filter without override and unlimited check
            3. Remove taxonomies assigned earlier to role and ensure
                no taxonomies are assigned to role
            4. List Role filter

        :expectedresults: Unlimited flag should be forcefully set on filter
            when no taxonomies are set to role and filter

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_user_group_users_access_as_org_admin(self):
        """Users in usergroup can have access to the resources in taxonomies if
        the taxonomies of Org Admin role is same

        :id: 630fcd05-5c27-44a7-9bea-fcef1143b252

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization A and Location A to both users
            5. Create an user group with above two users

        :expectedresults: Both users should have access to the resources of
            organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_user_group_users_access_contradict_as_org_admins(self):
        """Users in usergroup can/cannot have access to the resources in
        taxonomies depends on the taxonomies of Org Admin role is same/not_same

        :id: 55099979-de11-4730-83ce-e190a3b8ecaa

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an user without assigning roles while creating them and
                assign Organization B and Location B
            4. Create another user without assigning roles while creating them
                and assign Organization A and Location A
            5. Create an user group add above two users to the user group

        :expectedresults:

            1. User assigned to Organization B and Location B shouldn't have
                access to the resources of organization A,B and Location A,B
            2. User assigned to Organization A and Location A should have
                access to the resources of organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_assign_org_admin_to_user_group(self):
        """Users in usergroup can access to the resources in taxonomies if
        the taxonomies of Org Admin role are same

        :id: 07fa1bb4-1cce-4afa-a4f3-669704450947

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization A and Location A to both users
            5. Create an user group add above two users to the user group

        :expectedresults: Both the user should have access to the resources of
            organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_assign_org_admin_to_user_group(self):
        """Users in usergroup can not have access to the resources in
        taxonomies if the taxonomies of Org Admin role is not same

        :id: 81c076ba-d61c-4d03-96be-6db8458a2470

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization B and Location B to both users
            5. Create an user group add above two users to the user group

        :expectedresults: Both the user shouldn't have access to the resources
            of organization A,B and Location A,B

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_negative_assign_taxonomies_by_org_admin(self):
        """Org Admin doesn't have permissions to assign org/loc to any of
        its entities

        :id: da44d206-e5d9-4353-bc8c-dda99299fae4

        :steps:

            1. Create Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A,B and Location A,B to the Org Admin
                role
            3. Create user and assign above Org Admin role
            4. Assign Organization A,B and Location A,B to the user
            5. Attempt to assign organization(s) and location(s) to any
                resource from new user

        :expectedresults: Org Admin should not be able to assign the taxonomies
            to any of its resources

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_remove_org_admin_role(self):
        """Super Admin user can remove Org Admin role

        :id: 57ba763d-66b4-4f40-8e53-064141277960

        :steps:

            1. Create Org Admin by cloning 'Organization admin' role
            2. Assign any taxonomies to it
            3. Create an user and assign above role to user
            4. Delete the Org Admin role

        :expectedresults: Super Admin should be able to remove Org Admin role
        """

    @stubbed()
    @tier2
    def test_positive_taxonomies_control_to_superadmin_with_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin

        :id: bc5a3ad2-1f1f-4cda-a1ba-88b0f2e452c8

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Attempt to access entities in Organization A and Location A from
                superadmin user who created org admin

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_taxonomies_control_to_superAdmin_without_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin
        after deleting Org Admin role/user

        :id: 2ed27587-d25a-4cd6-9baa-74de9e035bf5

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Delete Org Admin role also the User created above
            4. Login with SuperAdmin who created the above Org Admin role and
                access entities in Organization A and Location A

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin after deleting Org Admin

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_negative_create_roles_by_org_admin(self):
        """Org Admin has no permissions to create new roles

        :id: 13fb38b6-2e38-4031-a57c-8ce75b333960

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above org Admin role to it
            3. Attempt to create a new role using Org Admin user

        :expectedresults: Org Admin should not have permissions to create
            new role
        """

    @stubbed()
    @tier1
    def test_negative_modify_roles_by_org_admin(self):
        """Org Admin has no permissions to modify existing roles

        :id: fa4a1b65-52b3-4920-9784-748dea8f51a0

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Attempt to update any existing role using Org Admin user

        :expectedresults: Org Admin should not have permissions to update
            existing roles
        """

    @stubbed()
    @tier2
    def test_negative_admin_permissions_to_org_admin(self):
        """Org Admin has no access to Super Admin user

        :id: 6903ed39-6e53-406e-abd9-634c7a749f1e

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to get super admin info command details

        :expectedresults: Org Admin should not have access of Admin user

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_create_user_by_org_admin(self):
        """Org Admin can create new users

        :id: 02f283ac-7d89-4622-be8e-640c775500c4

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Attempt to create new users

        :expectedresults:

            1. Org Admin should be able to create new users
            2. Only Org Admin role should be available to assign to its users
            3. Org Admin should be able to assign Org Admin role to its users

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_access_users_inside_org_admin_taxonomies(self):
        """Org Admin can access users inside its taxonomies

        :id: e9efce12-a017-4100-8262-c9db666fd890

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org A and Location A
            5. Assign any role to user B that does have access to Org A and
                Location A
            6. Login with Org Admin user A and attempt to view user B

        :expectedresults: Org Admin should be able to access users inside
            its taxonomies

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_negative_access_users_outside_org_admin_taxonomies(self):
        """Org Admin can not access users outside its taxonomies

        :id: 81081c75-031d-4aca-acd6-25868a492a84

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org B and Location B
            5. Assign any role to user B that doesnt have access to Org A and
                Location A
            6. Attempt to view user B using Org Admin user A

        :expectedresults: Org Admin should not be able to access users outside
            its taxonomies

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_negative_create_taxonomies_by_org_admin(self):
        """Org Admin cannot define/create organizations and locations

        :id: 115c46ea-f2fc-4be0-bbdb-26faf9246809

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Attempt to create Organizations and Locations using Org Admin
                user

        :expectedresults: Org Admin should not have access to create taxonomies
        """

    @stubbed()
    @tier1
    def test_negative_access_all_global_entities_by_org_admin(self):
        """Org Admin can access all global entities in any taxonomies
        regardless of its own assigned taxonomies

        :id: 6ebccf86-1766-432a-ad7c-4f2f606e1604

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user and assign Org A,B and Location A,B
            3. Assign Org Admin role to User
            4. Attempt to create all the global entities in org B and Loc B
                using Org Admin user. e.g Architectures, Operating System

        :expectedresults: Org Admin should have access to all the global
            entities in any taxonomies
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_access_entities_from_ldap_org_admin(self):
        """LDAP User can access resources within its taxonomies if assigned
        role has permission for same taxonomies

        :id: 086c7e50-4db9-4422-a960-d9702976e4e6

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with same taxonomies as role above
            3. Assign Org Admin role to user above
            4. Attempt to access resources from above LDAP user

        :expectedresults: LDAP User should be able to access all the resources
            and permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_org_admin(self):
        """LDAP User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 17a78a6d-d443-4700-8fd5-6a9336e96f91

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should not be able to access resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_user(self):
        """LDAP User can not access resources within its own taxonomies if
        assigned role does not have permissions for same taxonomies

        :id: e44614ab-7af3-40a1-a3a2-8d47041e0daa

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should not be able to access any resources
            and permissions in its own taxonomies

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can access to the resources in taxonomies if
        the taxonomies of Org Admin role are same

        :id: 552737df-24ef-4eb9-8054-e261c3dbf2b3

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization A and Location A to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults: Users in LDAP usergroup should have access to the
            resources in taxonomies if the taxonomies of Org Admin role are
            same

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can not have access to the resources in
        taxonomies if the taxonomies of Org Admin role is not same

        :id: c3385e14-f589-4101-b76a-59cd9d518cb8

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization B and Location B to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults: Users in LDAP usergroup should not have access to the
            resources in taxonomies if the taxonomies of Org Admin role is not
            same

        :CaseLevel: System
        """


class SystemAdminTestCases(CLITestCase):
    """Test class for System Admin role end to end CLI"""

    def tearDown(self):
        """Will reset the changed value of settings"""
        Settings.set({
            'name': "outofsync_interval",
            'value': "30"
        })

    @upgrade
    @tier3
    def test_system_admin_role_end_to_end(self):
        """Test System admin role with a end to end workflow

        :id: da6b3549-d1cf-44fc-869f-08d15d407fa2

        :steps:

            1. Create a System admin role user1
            2. Login with the user1 and change global settings
                "Out of sync interval" to 31
            3. Create user2 with system admin role
            4. Login with user2 to create a Organization
            5. Clone a Org-admin role
            6. Edit the Architecture Filter and search name  =  x86_64
            7. Create a User with Cloned Org admin
            8. Login with user.

        :expectedresults:

            1. User should be assigned with System Admin role.
            2. User with sys admin role should be able to update settings
            3. User with sys admin role should be able to create users and
                assign Organizations to them.
            4. System Admin role should be able to create Organization admins
            5. User with sys admin role should be able to edit filters on roles

        :CaseLevel: System
        """
        org = make_org()
        location = make_location()
        common_pass = gen_string('alpha')
        role = Role.info({'name': 'System admin'})
        system_admin_1 = make_user({
            'password': common_pass,
            'organization-ids': org['id'],
            'location-ids': location['id']
            })
        User.add_role({
            'id': system_admin_1['id'],
            'role-id': role['id']
            })
        Settings.with_user(
            username=system_admin_1['login'],
            password=common_pass).set({
                'name': "outofsync_interval",
                'value': "32"
                })
        sync_time = Settings.list({
            'search': 'name=outofsync_interval'
            })[0]
        # Asserts if the setting was updated successfully
        self.assertEqual('32', sync_time['value'])

        # Create another System Admin user using the first one
        system_admin = User.with_user(
                username=system_admin_1['login'],
                password=common_pass).create({
                    u'auth-source-id': 1,
                    u'firstname': gen_string('alpha'),
                    u'lastname': gen_string('alpha'),
                    u'login': gen_string('alpha'),
                    u'mail': '{0}@example.com'.format(gen_string('alpha')),
                    u'password': common_pass,
                    u'organizations': org['name'],
                    u'role-ids': role['id'],
                    u'locations': location['name']
                    })
        # Create the Org Admin user
        org_role = Role.with_user(
            username=system_admin['login'],
            password=common_pass).clone({
                'name': 'Organization admin',
                'new-name': gen_string('alpha'),
                'organization-ids': org['id'],
                'location-ids': location['id']
                })
        org_admin = User.with_user(
                username=system_admin['login'],
                password=common_pass).create({
                    u'auth-source-id': 1,
                    u'firstname': gen_string('alpha'),
                    u'lastname': gen_string('alpha'),
                    u'login': gen_string('alpha'),
                    u'mail': '{0}@example.com'.format(gen_string('alpha')),
                    u'password': common_pass,
                    u'organizations': org['name'],
                    u'role-ids': org_role['id'],
                    u'location-ids': location['id']
                    })
        # Assert if the cloning was successful
        self.assertIsNotNone(org_role['id'])
        org_role_filters = Role.filters({'id': org_role['id']})
        search_filter = None
        for arch_filter in org_role_filters:
            if arch_filter['resource-type'] == 'Architecture':
                search_filter = arch_filter
                break
        Filter.with_user(
            username=system_admin['login'],
            password=common_pass).update({
                'role-id': org_role['id'],
                'id': arch_filter['id'],
                'search': 'name=x86_64'
                })
        # Asserts if the filter is updated
        self.assertIn('name=x86_64',
                      Filter.info({
                          'id': search_filter['id']
                            }).values()
                      )
        org_admin = User.with_user(
            username=system_admin['login'],
            password=common_pass).info({'id': org_admin['id']})
        # Asserts Created Org Admin
        self.assertIn(org_role['name'], org_admin['roles'])
        self.assertIn(org['name'], org_admin['organizations'])
