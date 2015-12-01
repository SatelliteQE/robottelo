# -*- encoding: utf-8 -*-
"""Test class for Roles UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class Role(UITestCase):
    """Implements Roles tests from UI"""

    def test_create_role_basic(self):
        """@Test: Create new role

        @Feature: Role - Positive Create

        @Assert: Role is created

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.assertIsNotNone(self.role.search(name))

    def test_negative_create_role_invalid_names(self):
        """@Test: Create new role with invalid names

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    def test_positive_delete(self):
        """@Test: Delete an existing role

        @Feature: Role - Positive Delete

        @Assert: Role is deleted

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_role(session, name=name)
                    self.role.delete(name)

    def test_update_role_name(self):
        """@Test: Update role name

        @Feature: Role - Positive Update

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

    def test_update_role_permission(self):
        """@Test: Update role permissions

        @Feature: Role - Positive Update

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

    def test_update_role_org(self):
        """@Test: Update organization under selected role

        @Feature: Role - Positive Update

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
