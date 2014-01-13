# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Roles UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Role(Base):
    """
    Implements the CRUD functions for Roles
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name):
        """
        Creates new Role with default permissions
        """
        self.wait_until_element(locators["roles.new"]).click()

        if self.wait_until_element(locators["roles.name"]):
            self.find_element(locators["roles.name"]).send_keys(name)

            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new role '%s'" % name)

    def search(self, name):
        """
        Searches existing role from UI
        """
        self.search_entity(name, locators["roles.role"])

    def remove(self, name, really):
        """
        Delete existing role
        """
        self.delete_entity(name, really, locators["roles.role"],
                           locators['roles.delete'])

    def update(self, old_name, new_name=None,
               perm_type=None, permissions=None):
        """
        Update role name and permission
        """
        element = self.search(old_name)

        if element:
            element.click()
            if new_name:
                if self.wait_until_element(locators["roles.name"]):
                    self.field_update("roles.name", new_name)
            if perm_type:
                self.find_element(locators
                                  ["roles.perm_filter"]).send_keys(perm_type)
                strategy = locators["roles.perm_type"][0]
                value = locators["roles.perm_type"][1]
                element = self.wait_until_element((strategy,
                                                   value % perm_type))
                if element:
                    element.click()
                    self.wait_for_ajax()
                    for permission in permissions:
                        strategy = locators["roles.permission"][0]
                        value = locators["roles.permission"][1]
                        element = self.wait_until_element((strategy,
                                                           value % permission))
                        if element:
                            element.click()
                        else:
                            raise Exception(
                                "Could not find the permission '%s'"
                                % permission)
                    self.find_element(common_locators["submit"]).click()
                    self.wait_for_ajax()
        else:
            raise Exception("Could not find role '%s'" % old_name)
