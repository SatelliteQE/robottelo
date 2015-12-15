# -*- encoding: utf-8 -*-
"""Test class for UserGroup UI"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import make_usergroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class UserGroupTestCase(UITestCase):
    """Implements UserGroup tests from UI"""

    @classmethod
    def setUpClass(cls):
        super(UserGroupTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @skip_if_bug_open('bugzilla', 1142588)
    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create new Usergroup using different names

        @Feature: Usergroup - Positive Create

        @Assert: Usergroup is created successfully
        """
        user_name = gen_string('alpha')
        password = gen_string('alpha')
        # Create a new user
        entities.User(login=user_name, password=password).create()
        with Session(self.browser) as session:
            for group_name in generate_strings_list():
                with self.subTest(group_name):
                    make_usergroup(session, name=group_name, users=[user_name])
                    self.assertIsNotNone(self.usergroup.search(group_name))

    @skip_if_bug_open('bugzilla', 1142588)
    @tier1
    def test_negative_create_with_invalid_name(self):
        """@Test: Create a new UserGroup with invalid names

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup is not created
        """
        with Session(self.browser) as session:
            for group_name in invalid_values_list(interface='ui'):
                with self.subTest(group_name):
                    make_usergroup(
                        session, org=self.organization.name, name=group_name)
                    self.assertIsNotNone(self.usergroup.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNone(self.usergroup.search(group_name))

    @tier1
    def test_negative_create_with_same_name(self):
        """@Test: Create a new UserGroup with same name

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup cannot be created with existing name
        """
        group_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['name_haserror']))

    @skip_if_bug_open('bugzilla', 1142588)
    @tier1
    def test_positive_delete_empty(self):
        """@Test: Delete an empty Usergroup

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted
        """
        with Session(self.browser) as session:
            for group_name in generate_strings_list():
                with self.subTest(group_name):
                    make_usergroup(
                        session, org=self.organization.name, name=group_name)
                    self.usergroup.delete(group_name)

    @skip_if_bug_open('bugzilla', 1142588)
    @tier2
    def test_positive_delete_with_user(self):
        """@Test: Delete an Usergroup that contains a user

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted but not the added user
        """
        user_name = gen_string('alpha')
        group_name = gen_string('utf8')
        # Create a new user
        entities.User(
            login=user_name,
            password=gen_string('alpha'),
            organization=[self.organization],
        ).create()

        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=group_name,
                users=[user_name],
                org=self.organization.name,
            )
            self.usergroup.delete(group_name)
            self.assertIsNotNone(self.user.search(user_name))

    @skip_if_bug_open('bugzilla', 1142588)
    @tier1
    def test_positive_update_name(self):
        """@Test: Update usergroup with new name

        @Feature: Usergroup - Positive Update

        @Assert: Usergroup is updated
        """
        name = gen_string('alpha')
        user_name = gen_string('alpha')
        password = gen_string('alpha')
        # Create a new user
        entities.User(login=user_name, password=password).create()
        with Session(self.browser) as session:
            make_usergroup(session, name=name)
            self.assertIsNotNone(self.usergroup.search(name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.usergroup.update(name, new_name, users=[user_name])
                    self.assertIsNotNone(self.usergroup.search(new_name))
                    name = new_name  # for next iteration
