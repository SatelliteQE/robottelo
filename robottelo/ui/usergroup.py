# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements User groups UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class UserGroup(Base):
    """
    Implements the CRUD functions for User groups
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name, users=None):
        """
        Creates new usergroup
        """

        self.wait_until_element(locators["usergroups.new"]).click()

        if self.wait_until_element(locators["usergroups.name"]):
            self.find_element(locators["usergroups.name"]).send_keys(name)
            self.configure_entity(users, "usergroup_user")
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new usergroup '%s'" % name)

    def remove(self, name, really):
        """
        Delete existing usergroup
        """
        #No search bar available for usergroup; Issue:3953
        #element = self.search(name, locators['usergroups.delete'])
        strategy = locators["usergroups.delete"][0]
        value = locators["usergroups.delete"][1]
        element = self.wait_until_element((strategy, value % name))
        if element:
            element.click()
            self.handle_alert(really)
        else:
            raise Exception(
                "Could not find the usergroup '%s'" % name)

    def update(self, old_name, new_name=None,
               users=None, new_users=None):
        """
        Update usergroup name and its users
        """

        #No search bar available for usergroup; Issue:3953
        #element = self.search(old_name, locators['usergroups.usergroup'])
        strategy = locators["usergroups.usergroup"][0]
        value = locators["usergroups.usergroup"][1]
        element = self.wait_until_element((strategy, value % old_name))

        if element:
            element.click()
            if new_name:
                if self.wait_until_element(locators["usergroups.name"]):
                    self.field_update("usergroups.name", new_name)
            self.configure_entity(users, "usergroup_user",
                                  new_entity_list=new_users)
            self.wait_for_ajax()
        else:
            raise Exception("Could not find usergroup '%s'" % old_name)
