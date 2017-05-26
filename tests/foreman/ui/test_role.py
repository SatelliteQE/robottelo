# -*- encoding: utf-8 -*-
"""Test class for Roles UI

@Requirement: Role

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from random import choice

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import ROLES
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import tier1, skip_if_bug_open
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role, make_user
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


class RoleTestCase(UITestCase):
    """Implements Roles tests from UI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create new role using different names

        @id: 8170598b-cf3b-4ff7-9baa-bee73f90d255

        @expectedresults: Role is created successfully
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.assertIsNotNone(self.role.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new role using invalid names

        @id: 4159a2ad-0952-4196-9e3b-56c721d24355

        @expectedresults: Role is not created
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

        @id: c8bd515a-e556-4b98-a993-ec37f541ffc3

        @expectedresults: Role is deleted successfully
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.role.delete(name)

    @tier1
    def test_positive_update_name(self):
        """Update existing role name

        @id: c3ad9eed-6896-470d-9043-3fda37bbe489

        @expectedresults: Role is updated
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

        @id: d57abcf2-a42f-40db-a61c-61b56bcc55b9

        @expectedresults: Role is updated
        """
        name = gen_string('alpha')
        resource_type = 'Architecture'
        permissions = ['view_architectures', 'edit_architectures']
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(
                name,
                add_permission=True,
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

    @skip_if_bug_open('bugzilla', 1353788)
    @tier1
    def test_positive_clone_builtin(self):
        """Clone one of the builtin roles

        @id: e3e6af90-fb31-4de9-8f36-f50550d7f00e

        @expectedresults: New role is created.
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

    @skip_if_bug_open('bugzilla', 1353788)
    @tier1
    def test_positive_clone_custom(self):
        """Create custom role with permissions and clone it

        @id: a4367968-eae5-4b8a-9b5c-61824b261320

        @expectedresults: New role is created and contains all permissions
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        # Pick up custom permissions
        resource_type = 'Architecture'
        permissions = ['view_architectures', 'edit_architectures']
        with Session(self.browser) as session:
            # Create custom role with permissions
            make_role(session, name=name)
            self.role.update(
                name,
                add_permission=True,
                resource_type=resource_type,
                permission_list=permissions,
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

    @skip_if_bug_open('bugzilla', 1353788)
    @tier1
    def test_positive_assign_cloned_role(self):
        """Clone role and assign it to user

        @id: cbb17f37-9039-4875-981b-1f427b095ed1

        @expectedresults: User is created successfully

        @BZ: 1353788
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
            strategy, value = common_locators['entity_deselect']
            element = self.user.wait_until_element(
                (strategy, value % role_name))
            self.assertIsNotNone(element)

    @skip_if_bug_open('bugzilla', 1353788)
    @tier1
    def test_positive_delete_cloned(self):
        """Delete cloned role

        @id: 7f0a595b-2b27-4dca-b15a-02cd2519b2f7

        @expectedresults: Role is deleted

        @BZ: 1353788
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

        @id: 688ecb7d-1d49-494c-97cc-0d5e715f3bb1

        @expectedresults: filter was successfully created

        @BZ: 1315580

        @CaseImportance: Critical
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

    @tier1
    def test_positive_update_org(self):
        """Update organization for selected role

        @id: 593dfca9-18dc-46cf-a7b1-b32edad3550c

        @expectedresults: Role is updated
        """
        name = gen_string('alpha')
        org = entities.Organization().create()
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(
                name,
                add_permission=True,
                resource_type='Activation Keys',
                permission_list=['view_activation_keys'],
                organization=[org.name],
            )
