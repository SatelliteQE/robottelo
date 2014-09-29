# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for UserGroup UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo import entities
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_usergroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class UserGroup(UITestCase):
    """Implements UserGroup tests from UI"""

    org_name = None
    org_id = None

    def setUp(self):
        super(UserGroup, self).setUp()

        # Make sure to use the Class' org_name instance
        if UserGroup.org_name is None:
            org_name = gen_string("alpha", 6)
            org_attrs = entities.Organization(name=org_name).create()
            UserGroup.org_name = org_attrs['name']
            UserGroup.org_id = org_attrs['id']

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_positive_create_usergroup(self, group_name):
        """@Test: Create new Usergroup

        @Feature: Usergroup - Positive Create

        @Assert: Usergroup is created

        """

        user_name = gen_string("alpha", 6)
        password = gen_string("alpha", 6)
        # Create a new user
        entities.User(
            login=user_name,
            password=password,
        ).create()

        with Session(self.browser) as session:
            make_usergroup(session, name=group_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(group_name))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list(len1=256))
    def test_negative_create_usergroup_1(self, group_name):
        """@Test: Create a new UserGroup with 256 characters in name

        @Feature:  Usergroup - Negative Create

        @Assert:  Usergroup is not created

        """

        with Session(self.browser) as session:
            make_usergroup(session, org=self.org_name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.usergroup.search(group_name))

    @data(" ", "")
    def test_negative_create_usergroup_2(self, group_name):
        """@Test: Create a new UserGroup with blank and whitespace in name

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup is not created

        """

        with Session(self.browser) as session:
            make_usergroup(session, org=self.org_name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list())
    def test_negative_create_usergroup_3(self, group_name):
        """@Test: Create a new UserGroup with same name

        @Feature: Usergroup - Negative Create

        @Assert: Usergroup cannot be  created with existing name

        """

        with Session(self.browser) as session:
            make_usergroup(session, org=self.org_name, name=group_name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            make_usergroup(session, org=self.org_name, name=group_name)
            self.assertIsNotNone(self.usergroup.wait_until_element
                                 (common_locators["name_haserror"]))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_remove_empty_usergroup(self, group_name):
        """@Test: Delete an empty Usergroup

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted

        """

        with Session(self.browser) as session:
            make_usergroup(session, org=self.org_name, name=group_name)
            self.assertIsNotNone(self.usergroup.search(group_name))
            self.usergroup.delete(group_name, True)
            self.assertIsNotNone(self.usergroup.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.usergroup.search(group_name))

    @skip_if_bug_open('bugzilla', 1142588)
    @data(*generate_strings_list())
    def test_remove_usergroup(self, group_name):
        """@Test: Delete an Usergroup that contains a user

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted but not the added user

        """

        user_name = gen_string("alpha", 6)
        password = gen_string("alpha", 6)
        # Create a new user
        entities.User(login=user_name, password=password).create()

        with Session(self.browser) as session:
            make_usergroup(session, name=group_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(group_name))
            self.usergroup.delete(group_name, True)
            self.assertIsNotNone(self.usergroup.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.usergroup.search(group_name))
            self.assertIsNotNone(self.user.search
                                 (name=user_name, search_key="login"))

    @skip_if_bug_open('bugzilla', 1142588)
    @data({'name': gen_string("alpha", 6),
           'new_name': gen_string("alpha", 6)},
          {'name': gen_string("alphanumeric", 6),
           'new_name': gen_string("alphanumeric", 6)},
          {'name': gen_string("numeric", 6),
           'new_name': gen_string("numeric", 6)},
          {'name': gen_string("utf8", 6),
           'new_name': gen_string("utf8", 6)},
          {'name': gen_string("latin1", 6),
           'new_name': gen_string("latin1", 6)})
    def test_update_usergroup(self, test_data):
        """@Test: Update usergroup with name or users

        @Feature: Usergroup - Positive Update

        @Assert: Usergroup is updated

        """
        name = test_data['name']
        new_name = test_data['new_name']
        user_name = gen_string("alpha", 6)
        password = gen_string("alpha", 6)
        # Create a new user
        entities.User(login=user_name, password=password).create()
        with Session(self.browser) as session:
            make_usergroup(session, name=name)
            self.assertIsNotNone(self.usergroup.search(name))
            self.usergroup.update(name, new_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(new_name))
