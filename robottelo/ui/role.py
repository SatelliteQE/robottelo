# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Roles UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.common.constants import FILTER
from selenium.webdriver.support.select import Select


class Role(Base):
    """
    Implements the CRUD functions for Roles
    """

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
        element = self.search_entity(name, locators["roles.role"])
        return element

    def remove(self, name, really):
        """
        Delete existing role
        """
        self.delete_entity(name, really, locators["roles.role"],
                           locators['roles.delete'],
                           locators['roles.dropdown'])

    def update(self, name, new_name=None, add_permission=False,
               resource_type=None, permission_list=None, organization=None):
        """
        Update role name/permissions/org
        """
        element = self.search(name)

        if element:
            if new_name:
                element.click()
                if self.wait_until_element(locators["roles.name"]):
                    self.field_update("roles.name", new_name)
            if add_permission:
                strategy = locators['roles.dropdown'][0]
                value = locators['roles.dropdown'][1]
                dropdown = self.wait_until_element((strategy, value % name))
                dropdown.click()
                self.wait_until_element(locators
                                        ["roles.add_permission"]).click()
                if resource_type:
                    Select(self.find_element
                           (locators["roles.select_resource_type"])
                           ).select_by_visible_text(resource_type)
                    if permission_list:
                        self.configure_entity(permission_list,
                                              FILTER['role_permission'])
                if organization:
                    self.wait_until_element(tab_locators
                                            ["roles.tab_org"]).click()
                    self.configure_entity(organization, FILTER['role_org'])
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception("Could not find role '%s'" % name)
