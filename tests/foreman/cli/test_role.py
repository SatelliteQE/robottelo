# -*- encoding: utf-8 -*-
"""Test for Roles CLI

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_filter, make_role
from robottelo.cli.filter import Filter
from robottelo.cli.role import Role
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import stubbed, tier1, tier2
from robottelo.test import CLITestCase


class RoleTestCase(CLITestCase):
    """Test class for Roles CLI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create new roles with provided name

        :id: 6883177c-6926-428c-92ab-9effbe1372ae

        :Assert: Role is created and has correct name

        :BZ: 1138553

        :CaseLevel: Critical
        """
        for name in generate_strings_list(length=10):
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)

    @tier1
    def test_positive_create_with_filter(self):
        """Create new role with a filter

        :id: 6c99ee25-4e58-496c-af42-f8ad2da6cf07

        :assert: Role is created and correct filter is assigned

        :CaseLevel: Critical
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
    def test_positive_create_with_permission(self):
        """Create new role with a set of permission

        :id: 7cb2b2e2-ad4d-41e9-b6b2-c0366eb09b9a

        :assert: Role is created and has correct set of permissions

        :CaseLevel: Critical
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
            Role.filters({'id': role['id']})[0]['permissions'],
            permissions
        )

    @tier1
    def test_positive_delete_by_id(self):
        """Create a new role and then delete role by its ID

        :id: 351780b4-697c-4f87-b989-dd9a9a2ad012

        :Assert: Role is created and then deleted by its ID

        :CaseLevel: Critical
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

        :Assert: Role is created and its name is updated

        :CaseLevel: Critical
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


class CannedRoleTestCases(CLITestCase):
    """Implements Canned Roles tests from UI"""

    @stubbed
    @tier1
    def test_positive_create_role_with_taxonomies(self):
        """create role with taxonomies

        :id: 4ce9fd35-4d3d-47f7-8bc6-7cf0b3b2d2f5

        :steps: Create new role with taxonomies

        :assert: New role is created with taxonomies

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_create_role_without_taxonomies(self):
        """Create role without taxonomies

        :id: 4dc80114-9629-487f-805c-c14241bdcde1

        :steps: Create new role without any taxonomies

        :assert: New role is created without taxonomies

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_create_filter_without_override(self):
        """Create filter in role w/o overriding it

        :id: 247ab670-29e6-4c14-9140-51966f4632f4

        :steps:

            1. Create a role with taxonomies assigned
            2. Create filter in role without overriding it

        :assert:

            1. Filter w/o override is created in role
            2. The taxonomies of role are inherited to filter
            3. Override check is not marked by default in filters table

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_create_non_overridable_filter(self):
        """Create non overridable filter in role

        :id: c53713a3-d4b6-47a1-b19e-8d2020f98efd

        :steps:

            1. Create a filter to which taxonomies cannot be associated.
            e.g Architecture filter

        :assert:

            1. Filter is created without taxonomies
            2. Filter doesnt inherit taxonomies from role

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_negative_override_non_overridable_filter(self):
        """Override non overridable filter

        :id: 163313eb-4401-4bb0-bf9a-58030251643b

        :steps: Attempt to override a filter to which taxonomies cannot be
            associated.  e.g Architecture filter

        :assert: Filter is not overrided as taxonomies cannot be applied to
            that filter

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_create_overridable_filter(self):
        """Create overridable filter in role

        :id: 47816636-d215-45a8-9d21-495b1e193913

        :steps:

            1. Create a filter to which taxonomies can be associated.
            e.g Domain filter
            2. Override a filter with some taxonomies

        :assert:

            1. Filter is created with taxonomies
            2. Override check is set to true
            3. Filter doesnt inherits taxonomies from role

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_update_role_taxonomies(self):
        """Update role taxonomies which applies to its non-overrided filters

        :id: 988cf8c6-8f6e-49de-be54-d17085f260b6

        :steps: Update existing role with different taxonomies

        :assert: The taxonomies are applied only to non-overrided role filters

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_negative_update_role_taxonomies(self):
        """Update role taxonomies which doesnt applies to its overrided filters

        :id: 9d0d94fa-34ee-41a0-868d-4dc7d774fb02

        :steps: Update existing role with different taxonomies

        :assert: The overridden role filters are not updated

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier1
    def test_positive_disable_filter_override(self):
        """Unset override resets filter taxonomies

        :id: f00f4f1f-caee-47ac-b02e-7802300d08a8

        :steps:

            1. Create role with overridden filter having different taxonomies
               than its role.
            2. Unset the override flag in above role filter

        :assert: The taxonomies of filters resets/synced to role taxonomies

        :caseautomation: notautomated

        :CaseLevel: Critical
        """

    @stubbed
    @tier2
    def test_positive_access_resources_from_role_taxonomies(self):
        """Test user access resources from taxonomies of assigned role

        :id: 754cf23e-43ed-4d2b-b4ec-dacc77bc009d

        :steps:

            1. Create role with taxonomies
            2. Create resource(s) filter(s) without overriding them
            3. Create user with taxonomies same as role taxonomies
            4. Assign step 1 role to user

        :assert: User should be able to access the resource(s) of the assigned
            role

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed
    @tier2
    def test_negative_access_resources_outside_role_taxonomies(self):
        """Test user cannot access resources from non associated taxonomies to
        role

        :id: 8a82e935-c5f1-460f-b1ff-1203b9c88df9

        :steps:

            1. Create role with taxonomies
            2. Create resource(s) filter(s) without overriding them
            3. Create user with taxonomies not matching role taxonomies
            4. Assign step 1 role to user

        :assert: User should not be able to access the resource(s) that are not
            associated to assigned role

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
