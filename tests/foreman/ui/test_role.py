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
from robottelo.constants import ROLES
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import stubbed, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import make_domain, make_role, make_user, set_context
from robottelo.ui.locators import common_locators, menu_locators, tab_locators
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
        with Session(self.browser) as session:
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
        with Session(self.browser) as session:
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
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.role.delete(name)

    @tier1
    def test_positive_update_name(self):
        """Update existing role name

        :id: c3ad9eed-6896-470d-9043-3fda37bbe489

        :expectedresults: Role is updated

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
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
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.add_permission(
                name,
                resource_type=resource_type,
                permission_list=permissions,
            )
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            assigned_permissions = self.role.get_permissions(
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
        builtin_name = choice(ROLES)
        new_name = gen_string('alpha')
        with Session(self.browser):
            self.role.clone(builtin_name, new_name)
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            self.assertIsNotNone(self.role.search(new_name))
            # Ensure that cloned role contains correct resource types
            builtin_resources = self.role.get_resources(builtin_name)
            cloned_resources = self.role.get_resources(new_name)
            self.assertGreater(len(cloned_resources), 0)
            self.assertEqual(set(builtin_resources), set(cloned_resources))
            # And correct permissions for every resource type
            builtin_perms = self.role.get_permissions(
                builtin_name, builtin_resources)
            cloned_perms = self.role.get_permissions(
                new_name, cloned_resources)
            self.assertEqual(builtin_perms.keys(), cloned_perms.keys())
            for key in cloned_perms.keys():
                self.assertEqual(
                    set(builtin_perms[key]),
                    set(cloned_perms[key]),
                    "Permissions differs for {0} resource type".format(key)
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
        with Session(self.browser) as session:
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
            cloned_resources = self.role.get_resources(new_name)
            self.assertGreater(len(cloned_resources), 0)
            self.assertEqual(resource_type, cloned_resources[0])
            # and all permissions
            cloned_permissions = self.role.get_permissions(
                new_name, [resource_type])
            self.assertIsNotNone(cloned_permissions)
            self.assertEqual(
                set(permissions), set(cloned_permissions[resource_type]))

    @tier1
    def test_positive_assign_cloned_role(self):
        """Clone role and assign it to user

        :id: cbb17f37-9039-4875-981b-1f427b095ed1

        :expectedresults: User is created successfully

        :BZ: 1353788

        :CaseImportance: Critical
        """
        user_name = gen_string('alpha')
        role_name = gen_string('alpha')
        with Session(self.browser) as session:
            # Clone one of the builtin roles
            self.role.clone(choice(ROLES), role_name)
            # Create user wit this role
            make_user(
                session, username=user_name, roles=[role_name], edit=True)
            self.user.search_and_click(user_name)
            self.user.click(tab_locators['users.tab_roles'])
            element = self.user.wait_until_element(
                common_locators['entity_deselect'] % role_name)
            self.assertIsNotNone(element)

    @tier1
    def test_positive_delete_cloned(self):
        """Delete cloned role

        :id: 7f0a595b-2b27-4dca-b15a-02cd2519b2f7

        :expectedresults: Role is deleted

        :BZ: 1353788

        :CaseImportance: Critical
        """
        new_name = gen_string('alpha')
        with Session(self.browser):
            self.role.clone(choice(ROLES), new_name)
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            self.assertIsNotNone(self.role.search(new_name))
            self.role.delete(new_name)

    @tier1
    def test_positive_create_filter_admin_user_with_locs(self):
        """Attempt to create a role filter by admin user, who has 6+ locations
        assigned

        :id: 688ecb7d-1d49-494c-97cc-0d5e715f3bb1

        :expectedresults: filter was successfully created

        :BZ: 1315580

        :CaseImportance: Critical
        """
        locs = []
        for _ in range(6):
            locs.append(
                entities.Location(organization=[self.session_org]).create())
        self.session_user.location += locs
        self.session_user = self.session_user.update(['location'])
        self.assertTrue(
            {loc.id for loc in locs}.issubset(
                {loc.id for loc in self.session_user.location})
        )
        resource_type = 'Architecture'
        permissions = ['view_architectures', 'edit_architectures']
        role_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_role(session, name=role_name)
            self.assertIsNotNone(self.role.search(role_name))
            self.role.add_permission(
                role_name,
                resource_type=resource_type,
                permission_list=permissions,
            )
            self.assertIsNotNone(
                self.role.wait_until_element(common_locators['alert.success']))
            assigned_permissions = self.role.get_permissions(
                role_name, [resource_type])
            self.assertIsNotNone(assigned_permissions)
            self.assertEqual(
                set(permissions), set(assigned_permissions[resource_type]))


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
        with Session(self.browser) as session:
            make_role(
                session,
                name=name,
                locations=[self.role_loc],
                organizations=[self.role_org],
            )
            self.assertIsNotNone(self.role.search(name))

    @tier2
    def test_positive_create_filter_without_override(self):
        """Create filter in role w/o overriding it

        :id: a7f76f6e-6c13-4b34-b38c-19501b65786f

        :steps:

            1. Create a role with taxonomies (location and organization)
                assigned
            2. Create filter in role without overriding it
            3. Create user and assign new role to it
            4. Re-login into application using new user with a role

        :expectedresults:

            1. Filter w/o override is created in role
            2. The taxonomies of role are inherited to filter
            3. Override check is not marked by default in filters table
            4. User can access application sections specified in a filter
        """
        name = gen_string('alpha')
        username = gen_string('alpha')
        password = gen_string('alpha')
        domain_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(
                session,
                name=name,
                locations=[self.role_loc],
                organizations=[self.role_org],
            )
            self.assertIsNotNone(self.role.search(name))
            self.role.add_permission(
                name,
                resource_type='Domain',
                permission_list=['view_domains', 'create_domains'],
                override_check=True,
            )
            self.assertTrue(self.role.wait_until_element(
                common_locators['alert.success']))
            make_user(
                session,
                username=username,
                password1=password,
                password2=password,
                roles=[name],
                locations=[self.role_loc],
                organizations=[self.role_org],
                edit=True
            )
        with Session(self.browser, username, password) as session:
            set_context(session, org=self.role_org)
            set_context(session, loc=self.role_loc)
            make_domain(session, name=domain_name)
            self.assertIsNotNone(self.domain.search(domain_name))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.content'], timeout=3))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.configure'], timeout=3))

    @tier2
    def test_positive_create_non_overridable_filter(self):
        """Create non overridden filter in role

        :id: 5ee281cf-28fa-439d-888d-b1f9aacc6d57

        :steps:

            1. Create a filter in a role to which taxonomies (location and
                organization) cannot be associated.  e.g Architecture filter
            2. Create an user with taxonomies different than role and assign
                role to it
            3. Login as new user and attempt to acess the resources

        :expectedresults:

            1. Filter is created without taxonomies
            2. Override checkbox is not available to check
            3. User can access resources, permissions specified in a filter
            4. User have access in all taxonomies available to user
        """
        name = gen_string('alpha')
        username = gen_string('alpha')
        password = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(
                session,
                name=name,
                locations=[self.role_loc],
                organizations=[self.role_org],
            )
            self.assertIsNotNone(self.role.search(name))
            self.role.add_permission(
                name,
                resource_type='Architecture',
                permission_list=['view_architectures', 'edit_architectures'],
                override_check=False,
            )
            self.assertTrue(self.role.wait_until_element(
                common_locators['alert.success']))
            make_user(
                session,
                username=username,
                password1=password,
                password2=password,
                roles=[name],
                locations=[self.role_loc],
                organizations=[self.role_org],
                edit=True
            )
        with Session(self.browser, username, password) as session:
            set_context(session, org=self.role_org)
            set_context(session, loc=self.role_loc)
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.content'], timeout=3))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.infrastructure'], timeout=3))
            # check that we can access edit functionality at all
            self.architecture.update(old_name='x86_64', new_name='x86_64')

    @tier2
    def test_positive_create_overridable_filter(self):
        """Create overridden filter in role

        :id: 325e7e3e-60fc-4182-9585-0449d9660e8d

        :steps:

            1. Create a role with some taxonomies (organizations and locations)
            2. Create a filter in role to which taxonomies can be associated
                e.g Domain filter
            3. Override a filter with some taxonomies which doesnt match the
                taxonomies of role
            4. Create user with taxonomies including filter taxonomies and
                assign role to it
            5. Login with user and attempt to access the resources

        :expectedresults:

            1. Filter is created with taxonomies
            2. Override checkmark is displayed in filters table for that filter
            3. User can access resources, permissions specified in filter
            4. User have access only in taxonomies specified in filter
        """
        name = gen_string('alpha')
        username = gen_string('alpha')
        password = gen_string('alpha')
        domain_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(
                session,
                name=name,
                locations=[self.role_loc],
                organizations=[self.role_org],
            )
            self.assertIsNotNone(self.role.search(name))
            self.role.add_permission(
                name,
                resource_type='Domain',
                permission_list=['view_domains', 'create_domains'],
                override=True,
                override_check=True,
                organization=[self.filter_org],
                location=[self.filter_loc],
            )
            make_user(
                session,
                username=username,
                password1=password,
                password2=password,
                roles=[name],
                locations=[self.role_loc, self.filter_loc],
                organizations=[self.role_org, self.filter_org],
                edit=True
            )
        with Session(self.browser, username, password) as session:
            set_context(session, org=self.filter_org)
            set_context(session, loc=self.filter_loc)
            make_domain(session, name=domain_name)
            self.assertIsNotNone(self.domain.search(domain_name))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.content'], timeout=3))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.configure'], timeout=3))

        with Session(self.browser, username, password) as session:
            set_context(session, org=self.role_org)
            set_context(session, loc=self.role_loc)
            self.assertIsNone(self.domain.search(domain_name))
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['menu.hosts'], timeout=3))

    @stubbed
    @tier2
    def test_positive_update_role_taxonomies(self):
        """Update role taxonomies which applies only to non-overrided filters
        in role

        :id: f705faea-0d1c-4c11-b82d-b6b0e848f75d

        :steps:

            1. Create role with overrided, non-overrided resources and assign
                some taxonomies (organizations and locations) to role
            2. Assign this role to user
            3. Update existing role with different taxonomies
            4. Login with new user and attempt to access the resources

        :expectedresults:

            1. The role is updated successfully
            2. User should have access to non-overrided resources of role in
                updated taxonomies
            3. User shouldnt have access to overrided resources of role in
                updated taxonomies

        :caseautomation: notautomated
        """

    @stubbed
    @tier2
    def test_positive_disable_filter_override(self):
        """Uncheck override resets filter taxonomies

        :id: cae31e44-c3d6-4a08-a088-d12cb2088068

        :steps:

            1. Create role with some taxonomies (Organizations and Locations)
            2. Create and override filter having different taxonomies than its
                role
            3. Create user with role
            4. Uncheck the override checkbox in role filter
            5. Login with user and attempt to access resources

        :expectedresults:

            1. On unchecking override, the override mark is not displayed for
                that filter in filters table
            2. On unchecking override, User should have access to resources in
                taxonomies assigned to role
            3. On unchecking override, User shouldn't have access to resources
                in taxonomies mentioned in filter

        :caseautomation: notautomated
        """

    @stubbed
    @tier2
    def test_positive_disable_overriding_option(self):
        """Disable overriding option to disable single filter overriding

        :id: e692d114-1b0b-4106-afdb-cf894ea09acf

        :steps:

            1. Create role with some taxonomies (Organizations and Locations)
            2. Create and override filter having different taxonomies than its
                role
            3. Create user with role
            4. Click on 'Disable overriding' option of that filter in filters
                table
            5. Login with user and attempt to access resources

        :expectedresults:

            1. On unchecking override, the override mark is not displayed for
                that filter in filters table
            2. On unchecking override, User should have access to resources in
                taxonomies assigned to role
            3. On unchecking override, User shouldn't have access to resources
                in taxonomies mentioned in filter

        :caseautomation: notautomated
        """

    @stubbed
    @tier2
    def test_positive_disable_all_filters_overriding_option(self):
        """Disable all filters overriding option to disable all filters
        overriding in a role

        :id: 2942835a-f156-4211-ab7d-77e2b08fceac

        :steps:

            1. Create role with more than one overridden filters
            2. Create user with role
            3. Click on 'Disable all filters overriding' button in filters
                table in role
            4. Login with user and attempt to access resources

        :expectedresults:

            1. On disable, the overridden mark is disabled for all the
                overridden filters in role
            2. On disable, User should have access to resources in taxonomies
                (orgnizations and locations) assigned to role
            3. On disable, User shouldn't have access to resources in
                taxonomies mentioned in filter

        :caseautomation: notautomated
        """

    @stubbed
    @tier2
    def test_positive_create_org_admin(self):
        """Create Org admin role which has access to all the resources within
        organization

        :id: 03f41736-c5c5-414a-ab75-650cecd6f6cd

        :steps:

            1. Clone Manager role which has most resource permissions
            2. Assign taxonomies (organizations and locations) to the cloned
                role
            3. Add more missing resource permission to the cloned role to make
                it Org Admin having access to all resources
            4. Create user and assign org admin role
            5. Login with user and attempt to access resources

        :expectedresults:

            1. Successfully created Org Admin by cloning manager role
            2. Successfully assigned taxonomiess to role
            3. Missing resource filters are added successfully to the Org Admin
                role
            4. User is able to access all the resources, permissions only in
                taxonomies selected in org admin role
            5. User shouldnt be able to access resources, permissions in
                taxonomies not selected in org admin role

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_create_cloned_role_with_taxonomies(self):
        """Test taxonomies can be set on cloned role.

        :id: ad20f5c7-3df7-4b43-8a52-097c87676d07

        :steps:

            1. Attempt to clone any existing role(e.g Manager Role)
            2. Set new taxonomies (locations and organizations) to cloned role

        :expectedresults:

            1. While cloning, role has no taxonomies selected by default
            2. While cloning, role allows to set taxonomies
            3. New taxonomies should be applied to cloned role

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed
    @tier1
    def test_positive_override_cloned_role_filter(self):
        """Test if the cloned role filter can be overrided

        :id: e475aa7d-4844-4bb3-bfd3-3d4082a41fe4

        :steps:

            1. Clone any existing role(e.g Manager Role)
            2. Attempt to override the filter in cloned role

        :expectedresults: Filter in cloned role should be successfully
            overriding

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed
    @tier1
    def test_positive_empty_filter_taxonomies_in_cloned_role(self):
        """Test overridden filters taxonomies in cloned role

        :id: 86d9cd93-8189-45b3-86c6-ac9185e48655

        :steps: Clone a role having overridden filter(s), where filters should
            have some taxonomies (locations and organizations) assigned

        :expectedresults:

            1. On cloning, taxonomies of the overridden filters in cloned role
                are set to None
            2. Override mark is filters table is marked

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed
    @tier1
    def test_positive_override_empty_filter_taxonomies_in_cloned_role(self):
        """Override overridden filters in cloned role

        :id: 978bf745-0b63-4dc7-9512-77731b0caa23

        :steps:

            1. Clone a role having overridden filter(s)
            2. In cloned role, Assign some taxonomies (locations and
                organizations) to these filters as taxonomies in filters will
                be blank after cloning

        :expectedresults: In cloned role, The taxonomies should be able to
            assign to overridden filters

        :caseautomation: notautomated

        :CaseImportance: Critical
        """
