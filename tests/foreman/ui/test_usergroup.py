# -*- encoding: utf-8 -*-
"""Test class for UserGroup UI"""
from ddt import ddt, data
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_usergroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class UserGroup(UITestCase):
    """Implements UserGroup tests from UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(UserGroup, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_positive_create_usergroup(self, group_name):
        """@Test: Create new Usergroup

        @Feature: Usergroup - Positive Create

        @Assert: Usergroup is created

        """
        user_name = gen_string('alpha')
        password = gen_string('alpha')
        # Create a new user
        entities.User(login=user_name, password=password).create()

        with Session(self.browser) as session:
            make_usergroup(session, name=group_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(group_name))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list(len1=256))
    def test_negative_create_usergroup_with_too_long_name(self, group_name):
        """@Test: Create a new UserGroup with 256 characters in name

        @Feature:  Usergroup - Negative Create

        @Assert:  Usergroup is not created

        """
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['name_haserror']))
            self.assertIsNone(self.usergroup.search(group_name))

    @data('', ' ')
    def test_negative_create_usergroup_with_blank_name(self, group_name):
        """@Test: Create a new UserGroup with blank and whitespace in name

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup is not created

        """
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['name_haserror']))

    @data(*generate_strings_list())
    def test_negative_create_usergroup_with_same_name(self, group_name):
        """@Test: Create a new UserGroup with same name

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup cannot be  created with existing name

        """
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['name_haserror']))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_remove_empty_usergroup(self, group_name):
        """@Test: Delete an empty Usergroup

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted

        """
        with Session(self.browser) as session:
            make_usergroup(
                session, org=self.organization.name, name=group_name)
            self.usergroup.delete(group_name)

    @skip_if_bug_open('bugzilla', 1142588)
    def test_remove_usergroup(self):
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
            self.assertIsNotNone(self.user.search(
                name=user_name, search_key='login'))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_update_usergroup(self, new_name):
        """@Test: Update usergroup with name or users

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
            self.usergroup.update(name, new_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(new_name))
