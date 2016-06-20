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

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class RoleTestCase(UITestCase):
    """Implements Roles tests from UI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create new role using different names

        @id: 8170598b-cf3b-4ff7-9baa-bee73f90d255

        @Assert: Role is created successfully
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

        @Assert: Role is not created
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

        @Assert: Role is deleted successfully
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

        @Assert: Role is updated
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

        @Assert: Role is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(
                name,
                add_permission=True,
                resource_type='Architecture',
                permission_list=['view_architectures', 'create_architectures'],
            )

    @tier1
    def test_positive_update_org(self):
        """Update organization for selected role

        @id: 593dfca9-18dc-46cf-a7b1-b32edad3550c

        @Assert: Role is updated
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
