# -*- encoding: utf-8 -*-
"""Test class for Roles UI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    ROLES_LOCKED,
    ROLES_UNLOCKED,
)
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import stubbed, tier1, tier2, tier3, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class RoleTestCase(UITestCase):
    """Implements Roles tests from UI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create new role using different names

        :id: 8170598b-cf3b-4ff7-9baa-bee73f90d255

        :expectedresults: Role is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.assertIsNotNone(self.role.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new role using invalid names

        :id: 4159a2ad-0952-4196-9e3b-56c721d24355

        :expectedresults: Role is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_positive_delete(self):
        """Delete an existing role

        :id: c8bd515a-e556-4b98-a993-ec37f541ffc3

        :expectedresults: Role is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.role.delete(name, dropdown_present=True)

    @tier1
    def test_positive_update_name(self):
        """Update existing role name

        :id: c3ad9eed-6896-470d-9043-3fda37bbe489

        :expectedresults: Role is updated

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        with Session(self) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            for new_name in generate_strings_list(length=10):
                with self.subTest(new_name):
                    self.role.update(name, new_name)
                    self.assertIsNotNone(self.role.search(new_name))
                    name = new_name  # for next iteration

    @tier1
    def test_positive_update_permission(self):
        """Update existing role permissions

        :id: d57abcf2-a42f-40db-a61c-61b56bcc55b9

        :expectedresults: Role is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        resource_type = 'Architecture'
        permissions = ['view_architectures', 'edit_architectures']
        with Session(self) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.add_permission(
                name,
                resource_type=resource_type,
                permission_list=permissions,
            )
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            assigned_permissions = self.role.filters_get_permissions(
                name, [resource_type])
            self.assertIsNotNone(assigned_permissions)
            self.assertEqual(
                set(permissions), set(assigned_permissions[resource_type]))

    @tier1
    def test_positive_clone_builtin(self):
        """Clone one of the builtin roles

        :id: e3e6af90-fb31-4de9-8f36-f50550d7f00e

        :expectedresults: New role is created.

        :CaseImportance: Critical
        """
        builtin_names = [choice(ROLES_LOCKED), choice(ROLES_UNLOCKED)]
        with Session(self):
            for builtin_name in builtin_names:
                new_name = gen_string('alpha')
                with self.subTest(builtin_name):
                    self.role.clone(builtin_name, new_name)
                    self.assertIsNotNone(
                        self.role.wait_until_element(
                            common_locators['alert.success'])
                    )
                    self.assertIsNotNone(self.role.search(new_name))
                    # Ensure that cloned role contains correct resource types
                    builtin_resources = self.role.filters_get_resources(
                        builtin_name)
                    cloned_resources = self.role.filters_get_resources(
                        new_name)
                    self.assertGreater(len(cloned_resources), 0)
                    self.assertEqual(
                        set(builtin_resources), set(cloned_resources))
                    # And correct permissions for every resource type
                    builtin_perms = self.role.filters_get_permissions(
                        builtin_name, builtin_resources)
                    cloned_perms = self.role.filters_get_permissions(
                        new_name, cloned_resources)
                    self.assertEqual(builtin_perms.keys(), cloned_perms.keys())
                    for key in cloned_perms.keys():
                        self.assertEqual(
                            set(builtin_perms[key]),
                            set(cloned_perms[key]),
                            "Permissions differs for {0} resource type"
                            .format(key)
                        )

    @tier1
    def test_positive_clone_custom(self):
        """Create custom role with permissions and clone it

        :id: a4367968-eae5-4b8a-9b5c-61824b261320

        :expectedresults: New role is created and contains all permissions

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        # Pick up custom permissions
        resource_type = 'Architecture'
        permissions = ['view_architectures', 'edit_architectures']
        with Session(self) as session:
            # Create custom role with permissions
            make_role(session, name=name)
            self.role.add_permission(
                name, resource_type=resource_type, permission_list=permissions,
            )
            self.assertIsNotNone(self.role.search(name))
            # Clone role
            self.role.clone(name, new_name)
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            self.assertIsNotNone(self.role.search(new_name))
            # Ensure that cloned role contains correct resource types
            cloned_resources = self.role.filters_get_resources(new_name)
            self.assertGreater(len(cloned_resources), 0)
            self.assertEqual(resource_type, cloned_resources[0])
            # and all permissions
            cloned_permissions = self.role.filters_get_permissions(
                new_name, [resource_type])
            self.assertIsNotNone(cloned_permissions)
            self.assertEqual(
                set(permissions), set(cloned_permissions[resource_type]))


class CannedRoleTestCases(UITestCase):
    """Implements Canned Roles tests from UI"""

    @classmethod
    def setUpClass(cls):
        """Create Organization and Location to be used in tests"""
        super(CannedRoleTestCases, cls).setUpClass()
        cls.role_org = entities.Organization().create().name
        cls.role_loc = entities.Location().create().name
        cls.filter_org = entities.Organization().create().name
        cls.filter_loc = entities.Location().create().name

    @tier1
    def test_positive_create_role_with_taxonomies(self):
        """create role with taxonomies

        :id: 5d9da688-f371-4654-93d3-b221211be280

        :steps: Create new role with taxonomies (location and organization)

        :expectedresults: New role is created with taxonomies

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_role(
                session,
                name=name,
                locations=[self.role_loc],
                organizations=[self.role_org],
            )
            self.assertIsNotNone(self.role.search(name))

    @stubbed()
    @tier1
    def test_negative_update_role_taxonomies_overridden_filters(self):
        """Update of role taxonomies doesnt applies on its overridden filters

        :id: 378ec15b-deed-4b1e-8e04-06642d2632a6

        :steps:

            1. Create role with organization A and Location A
            2. Add overridden filter in above role with Organization A and
                Location A
            3. Save the role with filter
            4. Edit the role and update Organization to B and Location to B
            5. Save the updates of role
            6. Reopen above role and view its overridden filter taxonomies

        :expectedresults: The taxonomies of overridden filter should not be
            updated with role taxonomies
        """

    @stubbed()
    @tier2
    def test_positive_override_checkmark(self):
        """Checkmark image for overridden role filters

        :id: ae7fa2f8-4887-4905-8139-91dc2d356d74

        :steps:

            1. Create role with an overridden filter
            2. View that filter in filters table list or role

        :expectedresults: The checkmark image should be displayed for
            overridden filter in filters table column of role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_disable_filter_override(self):
        """Uncheck override resets filter taxonomies

        :id: cae31e44-c3d6-4a08-a088-d12cb2088068

        :steps:

            1. Create role organization A and Location A
            2. Create an overridden filter in role with organization B
                and Location B
            3. Save above role with filter
            4. Reopen role filter and uncheck the override checkbox in role
                filter

        :expectedresults: On unchecking override, the override mark is not
            displayed for that filter in filters table

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_disable_overriding_option(self):
        """Disable overriding option to disable single filter overriding

        :id: e692d114-1b0b-4106-afdb-cf894ea09acf

        :steps:

            1. Create role with org A and Location A
            2. Create and override filter in role with Org B and Location B
            3. Save above role with filter
            4. Click on 'Disable overriding' option of that filter in filters
                table

        :expectedresults: On unchecking override, the override mark is not
            displayed for that filter in filters table

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_disable_all_filters_overriding_option(self):
        """Disable all filters overriding option to disable all filters
        overriding in a role

        :id: 2942835a-f156-4211-ab7d-77e2b08fceac

        :steps:

            1. Create role with org A and Location A
            2. Create more than one overridden filters in role with org B and
                Location B
            3. Save above role with filters
            4. Click on 'Disable all filters overriding' button in filters
                table in role

        :expectedresults: On disable, the overridden mark is disabled for all
            the overridden filters in role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_create_org_admin_from_clone(self):
        """Create Org Admin role which has access to most of the resources
        within organization

        :id: 03f41736-c5c5-414a-ab75-650cecd6f6cd

        :steps:

            1. create Org Admin by cloning 'Organization admin' role which has
                most resources permissions

        :expectedresults: Org Admin should be created successfully

        :caseautomation: notautomated
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_cloned_role_with_taxonomies(self):
        """Taxonomies can be assigned to cloned role

        :id: ad20f5c7-3df7-4b43-8a52-097c87676d07

        :steps:

            1. Create Org Admin by cloning 'Organization admin' role
            2. Set new taxonomies (locations and organizations) to cloned role

        :expectedresults:

            1. While cloning, role has no taxonomies selected by default
            2. While cloning, role allows to set taxonomies
            3. New taxonomies should be applied to cloned role successfully

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_access_entities_from_org_admin(self):
        """User can access resources within its taxonomies if assigned role
        has permission for same taxonomies

        :id: dcdc438a-a8f0-4b3e-a8cb-e6f5c9215b1b

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with same taxonomies as role above
            3. Assign cloned role to user above
            4. Login with user and attempt to access resources

        :expectedresults: User should be able to access all the resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_org_admin(self):
        """User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 1f7225ed-0bd0-4d31-9af0-3c74e8ccfb42

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user
            4. Login with user and attempt to access resources

        :expectedresults: User should not be able to access any resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_user(self):
        """User can not access resources within its own taxonomies if assigned
        role does not have permissions for same taxonomies

        :id: ec5fc7d9-0150-465f-b5b0-ff21d75b8e8e

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to user.
            4. Login with user and attempt to access resources

        :expectedresults: User shoule not be able to access any resources and
            permissions in his own taxonomies

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_override_cloned_role_filter(self):
        """Cloned role filter overrides

        :id: e475aa7d-4844-4bb3-bfd3-3d4082a41fe4

        :steps:

            1. Create a role with overridable filter.
            2. Clone above role.
            3. Attempt to override the filter in cloned role

        :expectedresults: Filter in cloned role should be overriding

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_emptiness_of_filter_taxonomies_on_role_clone(self):
        """Taxonomies of filters in cloned role are set to None for filters that
        are overridden in parent role

        :id: 86d9cd93-8189-45b3-86c6-ac9185e48655

        :steps:

            1. Create a role with an overridden filter
            2. Overridden filter should have taxonomies assigned
            3. Clone above role
            4. View cloned role filters

        :expectedresults:

            1. Taxonomies of the 'parent role overridden filters' are set to
                None in cloned role
            2. Override mark is filters table is marked

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_override_empty_filter_taxonomies_in_cloned_role(self):
        """Taxonomies of filters in cloned role can be overridden for filters that
        are overridden in parent role

        :id: 978bf745-0b63-4dc7-9512-77731b0caa23

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
        sets on filter for filter that is overridden in parent role

        :id: 956b2c06-83e7-49ca-aca3-b60be8288f1b

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Save above role with filter
            4. Clone above role and assign Organization A and Location A
                while cloning
            5. View cloned role filter

        :expectedresults: Unlimited and Override should be set on filter for
            filter that is overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_non_overridden_filter_with_taxonomies(self):# noqa
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter for filter that is not overridden in parent
        role

        :id: cef06d24-e2aa-4605-ae2c-de6d6da14cd3

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Save above role with filter
            4. Clone above role and assign Organization A and Location A
                while cloning
            5. View cloned role filter

        :expectedresults: Neither unlimited nor override should be set on
            filter for filter that is not overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_unlimited_filter_with_taxonomies(self):
        """When taxonomies assigned to cloned role, Neither unlimited nor
        override sets on filter for filter that is unlimited in parent role

        :id: 0d102569-8769-4ad5-bfe2-c851c7a6c0b1

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Save above role with filter
            4. Clone above role and assign Organization A and Location A
                while cloning
            5. View cloned role filter

        :expectedresults: Neither unlimited nor override should be set on
            filter for filter that is unlimited in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_having_overridden_filter_without_taxonomies(self):# noqa
        """When taxonomies not assigned to cloned role, Unlimited and override
        checks sets on filter for filter that is overridden in parent role

        :id: d75fb125-07a4-485e-8a45-16c685199c86

        :steps:

            1. Create a role with organization A and Location A
            2. Create overridden role filter in organization B
                and Location B
            3. Save above role with filter
            4. Clone above role without assigning taxonomies
            5. View cloned role filter

        :expectedresults: Unlimited and Override should be set on
            filter for filter that is overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_without_taxonomies_non_overided_filter(self):
        """When taxonomies not assigned to cloned role, only unlimited but not
        override check sets on filter for filter that is overridden in parent
        role

        :id: fcfa8706-90b9-4ff3-bf5a-ec7c0e00d9d7

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter without overriding
            3. Save above role with filter
            4. Clone above role without assigning taxonomies
            5. View cloned role filter

        :expectedresults:

            1. Unlimited check should be set on filter for filter that is not
                overridden in parent role
            2. Override check should not be set on filter for filter that is
                not overridden in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_clone_role_without_taxonomies_unlimited_filter(self):
        """When taxonomies not assigned to cloned role, Unlimited and override
        checks sets on filter for filter that is unlimited in parent role

        :id: eb7f0c4e-e09b-4630-965d-326179426f9e

        :steps:

            1. Create a role with organization A and Location A
            2. Create role filter with unlimited check
            3. Save above role with filter
            4. Clone above role without assigning taxonomies
            5. View cloned role filter

        :expectedresults:

            1. Unlimited check should be set on filter for filter that
                unlimited in parent role
            2. Override check should not be set on filter for filter that is
                unlimited in parent role

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_force_unlimited(self):
        """Unlimited check forced sets to filter when no taxonomies are set to role
        and filter

        :id: ae79dc4b-dcf1-45cf-8411-b768beb66bc2

        :steps:

            1. Create a role with organization A and Location A
            2. Create a role filter without override and unlimited check
            3. Save above role and filter
            4. Edit the role and remove taxonomies assigned earlier and ensure
                no taxonomies are assigned to role
            5. View Role filter

        :expectedresults: Unlimited check should be forcefully sets on filter
            when no taxonomies are set to role and filter

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_user_group_users_access_as_org_admin(self):
        """Users in usergroup can have access to the resources in taxonomies if
        the taxonomies of Org Admin role is same

        :id: a96d98bc-9ef5-4659-a470-939995ef148c

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization A and Location A to both users
            5. Create an user group add above two users to the user group

        :expectedresults:

            1. Both the user should list Org Admin role inherited from
                usergroup
            2. Both the user should have access to the resources of
                organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_user_group_users_access_contradict_as_org_admins(self):
        """Users in usergroup can/cannot have access to the resources in
        taxonomies depends on the taxonomies of Org Admin role is same/not_same

        :id: 358db64e-41ab-42e5-a5e4-66f19f342f88

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an user without assigning roles while creating them and
                assign Organization B and Location B
            4. Create another user without assigning roles while creating them
                and assign Organization A and Location A
            5. Create an user group add above two users to the user group

        :expectedresults:

            1. Both the user should list role inherited from usergroup
            2. User assigned to Organization B and Location B shouldn't have
                access to the resources of organization A,B and Location A,B
            3. User assigned to Organization A and Location A should have
                access to the resources of organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_assign_org_admin_to_user_group(self):
        """Users in usergroup can access to the resources in taxonomies if
        the taxonomies of Org Admin role are same

        :id: d49fc7c6-b177-4666-a144-bb80eec6e1c0

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization A and Location A to both users
            5. Create an user group add above two users to the user group

        :expectedresults:

            1. Both the user should list role inherited from usergroup
            2. Both the user should have access to the resources of
                organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_assign_org_admin_to_user_group(self):
        """Users in usergroup can not have access to the resources in taxonomies if
        the taxonomies of Org Admin role is not same

        :id: 3b87f81a-2c9f-48e0-8bf1-863af335dd52

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create two users without assigning roles while creating them
            4. Assign Organization B and Location B to both users
            5. Create an user group add above two users to the user group

        :expectedresults:

            1. Both the user should list role inherited from usergroup
            2. Both the user shouldn't have access to the resources of
                organization A,B and Location A,B

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_negative_assign_taxonomies_by_org_admin(self):
        """Org Admin doesn't have permissions to assign org/loc to any of
        its entities

        :id: 61a99863-801a-4d66-963b-9699ff1a3236

        :steps:

            1. Create Org Admin by cloning 'Organization admin' role
            2. Assign an organization A,B and Location A,B to the Org Admin
                role
            3. Create user and assign above Org Admin role
            4. Assign Organization A,B and Location A,B to the user
            5. Login from the new user and attempt to assign organization(s)
                and location(s) to any resource

        :expectedresults: No Organization and Location tabs are available in
            resource for Org Admin to assign the taxonomies

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_remove_org_admin_role(self):
        """Super Admin user can remove Org Admin role

        :id: 9ef6e960-0775-4b1a-a17b-5bcbc4a865a9

        :steps:

            1. Create Org Admin by cloning 'Organization admin' role
            2. Assign any taxonomies to it
            3. Create an user and assign above role to user
            4. Delete the Org Admin role

        :expectedresults: Super Admin should be able to remove Org Admin role
        """

    @stubbed()
    @tier2
    def test_positive_taxonomies_control_to_superAdmin_with_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin

        :id: e617eadc-346a-4692-8266-f41e4739813e

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Login with SuperAdmin who created the above Org Admin role and
                access entities in Organization A and Location A

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin in Org Admin's presence

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_taxonomies_control_to_superAdmin_without_org_admin(self):
        """Super Admin can access entities in taxonomies assigned to Org Admin
        after deleting Org Admin role/user

        :id: a0ef30e4-f760-466a-a5e0-2eb954120166

        :steps:

            1. Create Org Admin role and assign organization A and Location A
            2. Create User and assign above Org Admin role
            3. Delete Org Admin role and User created above
            4. Login with SuperAdmin who created the above Org Admin role and
                access entities in Organization A and Location A

        :expectedresults: Super admin should be able to access the entities in
            taxonomies assigned to Org Admin after deleting Org Admin's
            role/user

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_negative_create_roles_by_org_admin(self):
        """Org Admin has no permissions to create new roles

        :id: cd81fbd8-790d-4a2f-bdac-f0eaebe234d4

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above org Admin role to it
            3. Login with above Org Admin user
            4. Go to Administer -> Roles, attempt to create a new role

        :expectedresults: Org Admin should not have permissions to create
            new role
        """

    @stubbed()
    @tier1
    def test_negative_modify_roles_by_org_admin(self):
        """Org Admin has no permissions to modify existing roles

        :id: 8fe0b33e-e919-46dd-90f0-d177ddf40fde

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Go to Administer -> Roles, attempt to edit any existing role
                to modify

        :expectedresults: Org Admin should not have permissions to edit/modify
            existing roles
        """

    @stubbed()
    @tier2
    def test_negative_admin_permissions_to_org_admin(self):
        """Org Admin has no access to Super Admin user

        :id: ad3d27c3-176b-4560-883d-629015db77cb

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Go to Administer -> Users, Attempt to view 'Super Admin' user

        :expectedresults: Org Admin should not have view access of Admin user

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_create_user_by_org_admin(self):
        """Org Admin can create new users

        :id: fd173222-02f6-49b8-95a9-cf25c61f9f4a

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Go to Administer -> Users, Attempt to create new users

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

        :id: b8448d5d-67fe-4818-b0c6-902770f21bab

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org A and Location A
            5. Assign any role to user B that does have access to Org A and
                Location A
            6. Login with Org Admin user A
            7. Go to Administer -> Users and attempt to view user B

        :expectedresults: Org Admin should be able to access users inside
            its taxonomies

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_negative_access_users_outside_org_admin_taxonomies(self):
        """Org Admin can not access users outside its taxonomies

        :id: 1d5feebe-e10c-4293-a994-9c2d9aee0a2d

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user A and assign Org A and Location A
            3. Assign Org Admin role to User A
            4. Create another user B and assign Org B and Location B
            5. Assign any role to user B that doesnt have access to Org A and
                Location A
            6. Login with Org Admin user A
            7. Go to Administer -> Users and attempt to view user B

        :expectedresults: Org Admin should not be able to access users outside
            its taxonomies

        :CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_negative_create_taxonomies_by_org_admin(self):
        """Org Admin cannot define/create organizations and locations

        :id: 2f8afb04-0793-463c-aed8-6818f8c4068c

        :steps:

            1. Create Org Admin role and assign any taxonomies to it
            2. Create user and assign above Org Admin role to it
            3. Login with above Org Admin user
            4. Go to Context Switcher, check if 'Manage Organizations' and
                'Manage Locations' links are available

        :expectedresults: Org Admin should not have access to create taxonomies
        """

    @stubbed()
    @tier1
    def test_negative_access_all_global_entities_by_org_admin(self):
        """Org Admin can access all global entities regardless of their
        taxonomies

        :id: 4e7662c0-5bb5-4b7c-810c-edab08358b3f

        :steps:

            1. Create Org Admin role and assign Org A and Location A
            2. Create new user and assign Org A,B and Location A,B
            3. Assign Org Admin role to User
            4. Login with Org Admin user
            5. Attempt to create all the global entities in org B and Loc B
                to which Org Admin doesnt have permissions
                e.g Architectures, Operating System

        :expectedresults: Org Admin should have access to all the global
            entities
        """

    @stubbed()
    @tier3
    def test_positive_access_entities_from_ldap_org_admin(self):
        """LDAP User can access resources within its taxonomies if assigned
        role has permission for same taxonomies

        :id: 05748c11-9d01-4d37-b3e8-c3583b41f4ec

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with same taxonomies as role above
            3. Assign Org Admin role to user above
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should be able to access all the resources
            and permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_org_admin(self):
        """LDAP User can not access resources in taxonomies assigned to role if
        its own taxonomies are not same as its role

        :id: 571c60f0-c23c-4009-804a-a3dd276013c9

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should be able to access any resources and
            permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_access_entities_from_ldap_user(self):
        """LDAP User can not access resources within its own taxonomies if
        assigned role does not have permissions for same taxonomies

        :id: d8c531a4-b167-4550-9547-6e5f9c888031

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with different taxonomies than above Org Admin
                taxonomies
            3. Assign above cloned role to LDAP user
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should not be able to access any resources
            and permissions in his own taxonomies

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can access to the resources in taxonomies if
        the taxonomies of Org Admin role are same

        :id: d60b208d-4cc4-4a5c-bc8f-d2583672b4b9

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization A and Location A to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults:

            1. Both the LDAP users should list role inherited from LDAP
                usergroup
            2. Both the LDAP users should have access to the resources of
                organization A and Location A

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_assign_org_admin_to_ldap_user_group(self):
        """Users in LDAP usergroup can not have access to the resources in
        taxonomies if the taxonomies of Org Admin role is not same

        :id: 7d2bef50-331e-417f-bba9-61affcb36593

        :steps:

            1. Create an Org Admin role by cloning 'Organization admin' role
            2. Assign an organization A and Location A to the Org Admin role
            3. Create an LDAP usergroup with two users
            4. Assign Organization B and Location B to LDAP usergroup
            5. Assign Org Admin role to LDAP usergroup

        :expectedresults:

            1. Both the LDAP user should list role inherited from LDAP
                usergroup
            2. Both the LDAP user shouldn't have access to the resources of
                organization A,B and Location A,B

        :CaseLevel: System
        """
