# -*- encoding: utf-8 -*-
"""Test class for Roles UI"""

from ddt import ddt, data
from fauxfactory import gen_string
from nailgun import entities
from robottelo.helpers import generate_strings_list, invalid_names_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_role
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Role(UITestCase):
    """Implements Roles tests from UI"""

    @data(*generate_strings_list(len1=10))
    def test_create_role_basic(self, name):
        """@Test: Create new role

        @Feature: Role - Positive Create

        @Assert: Role is created

        """
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))

    @data('', ' ')
    def test_negative_create_role_with_blank_name(self, name):
        """@Test: Create new role with blank and whitespace in name

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['name_haserror']))

    @data(*invalid_names_list())
    def test_negative_create_role_with_too_long_names(self, name):
        """@Test: Create new role with 256 characters in name

        @Feature: Role - Negative Create

        @Assert: Role is not created

        """
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['name_haserror']))

    @data(*generate_strings_list(len1=10))
    def test_remove_role(self, name):
        """@Test: Delete an existing role

        @Feature: Role - Positive Delete

        @Assert: Role is deleted

        """
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.role.delete(name)

    @data(*generate_strings_list(len1=10))
    def test_update_role_name(self, new_name):
        """@Test: Update role name

        @Feature: Role - Positive Update

        @Assert: Role is updated

        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_role(session, name=name)
            self.assertIsNotNone(self.role.search(name))
            self.role.update(name, new_name)
            self.assertIsNotNone(self.role.search(new_name))

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
