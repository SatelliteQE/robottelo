# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for UserGroup UI"""

from ddt import ddt
from robottelo import entities
from robottelo.common.decorators import data
from robottelo.orm import StringField
from robottelo.test import UITestCase
from robottelo.ui.factory import make_usergroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


def valid_usergroup_list():
    """List of valid data for input testing."""

    return [
        StringField(len=(5, 80), str_type=('alpha',)).get_value(),
        StringField(len=(5, 80), str_type=('alphanumeric',)).get_value(),
        StringField(len=(5, 80), str_type=('numeric',)).get_value(),
    ]


@ddt
class UserGroup(UITestCase):
    """Implements UserGroup tests from UI"""

    org_name = None
    org_id = None

    def setUp(self):
        super(UserGroup, self).setUp()

        # Make sure to use the Class' org_name instance
        if UserGroup.org_name is None:
            org_name = StringField(str_type=('alphanumeric',),
                                   len=(5, 80)).get_value()
            org_attrs = entities.Organization(name=org_name).create()
            UserGroup.org_name = org_attrs['name']
            UserGroup.org_id = org_attrs['id']

    @data(*valid_usergroup_list())
    def test_positive_create_usergroup(self, group_name):
        """@Test: Create new Usergroup

        @Feature: Usergroup - Positive Create

        @Assert: Usergroup is created

        """

        user_name = StringField(str_type=('alpha',)).get_value()
        password = StringField(str_type=('alpha',)).get_value()
        # Create a new user
        entities.User(
            login=user_name,
            password=password,
        ).create()

        with Session(self.browser) as session:
            make_usergroup(session, name=group_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(group_name))

    def test_negative_create_usergroup_1(self):
        """@Test: Create a new UserGroup with 256 characters in name

        @Feature:  Usergroup - Negative Create

        @Assert:  Usergroup is not created

        """
        group_name = StringField(str_type=('alphanumeric',),
                                 len=256).get_value()
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

    @data(*valid_usergroup_list())
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

    @data(*valid_usergroup_list())
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

    @data(*valid_usergroup_list())
    def test_remove_usergroup(self, group_name):
        """@Test: Delete an Usergroup that contains a user

        @Feature: Usergroup - Positive Delete

        @Assert: Usergroup is deleted but not the added user

        """

        user_name = StringField(str_type=('alpha',)).get_value()
        password = StringField(str_type=('alpha',)).get_value()
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

    @data({'name': StringField(str_type=('alpha',)).get_value(),
           'new_name': StringField(str_type=('alpha',)).get_value()},
          {'name': StringField(str_type=('alphanumeric',)).get_value(),
           'new_name': StringField(str_type=('alphanumeric',)).get_value()},
          {'name': StringField(str_type=('numeric',)).get_value(),
           'new_name': StringField(str_type=('numeric',)).get_value()})
    def test_update_usergroup(self, test_data):
        """@Test: Update usergroup with name or users

        @Feature: Usergroup - Positive Update

        @Assert: Usergroup is updated

        """
        name = test_data['name']
        new_name = test_data['new_name']
        user_name = StringField(str_type=('alpha',)).get_value()
        password = StringField(str_type=('alpha',)).get_value()
        # Create a new user
        entities.User(login=user_name, password=password).create()
        with Session(self.browser) as session:
            make_usergroup(session, name=name)
            self.assertIsNotNone(self.usergroup.search(name))
            self.usergroup.update(name, new_name, users=[user_name])
            self.assertIsNotNone(self.usergroup.search(new_name))
