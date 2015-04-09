# -*- encoding: utf-8 -*-
"""
Implements Environment UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from robottelo.common.constants import FILTER


class Environment(Base):
    """
    Provides the CRUD functionality for Environment.
    """

    def create(self, name, orgs, org_select=True):
        """
        Creates the environment.
        """
        self.wait_until_element(locators["env.new"]).click()
        if self.wait_until_element(locators["env.name"]):
            self.find_element(locators["env.name"]).send_keys(name)
        if orgs:
            self.configure_entity(orgs, FILTER['env_org'],
                                  tab_locator=tab_locators["tab_org"],
                                  entity_select=org_select)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def update(self, old_name, orgs=None, new_orgs=None, new_name=None,
               org_select=False):
        """
        Updates an environment.
        """
        element = self.search(old_name)
        if element:
            element.click()
            if self.wait_until_element(locators["env.name"]) and new_name:
                self.field_update("env.name", new_name)
            self.configure_entity(orgs, FILTER['env_org'],
                                  tab_locator=tab_locators["tab_org"],
                                  new_entity_list=new_orgs,
                                  entity_select=org_select)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing env from UI
        """
        Navigator(self.browser).go_to_environments()
        if len(name) <= 30:
            element = self.search_entity(name, locators["env.env_name"])
        else:
            element = self.search_entity(
                name, common_locators["select_filtered_entity"])
        return element

    def delete(self, name, really):
        """
        Deletes the environment.
        """

        self.delete_entity(name, really, locators["env.env_name"],
                           locators['env.delete'],
                           drop_locator=locators["env.dropdown"])
