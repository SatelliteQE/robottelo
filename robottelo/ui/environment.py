# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Environment UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators


class Environment(Base):
    """
    Provides the CRUD functionality for Environment.
    """

    def __init__(self, browser):
        self.browser = browser

    def _select_deselect_orgs(self, loc, org_list):
        """
        Selects and Deselects org association with environments.
        """
        for org in org_list:
            strategy = loc[0]
            value = loc[1]
            element = self.wait_until_element((strategy, value % org))
            element.click()

    def _configure_env(self, orgs, new_orgs=None, org_select=True):
        """
        Configures environment details like, orgs.
        """
        if orgs:
            org_tab_loc = tab_locators["environment.tab_org"]
            self.wait_until_element(org_tab_loc).click()
            if org_select:
                org_locator = locators["env.org_select"]
            else:
                org_locator = locators["env.org_deselect"]
            self._select_deselect_orgs(org_locator, orgs)
        if new_orgs:
            org_locator = locators["env.org_select"]
            self._select_deselect_orgs(org_locator, new_orgs)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def create(self, name, orgs, org_select=True):
        """
        Creates the environment.
        """
        self.wait_until_element(locators["env.new"]).click()
        if self.wait_until_element(locators["env.name"]):
            self.find_element(locators["env.name"]).send_keys(name)
        self._configure_env(orgs, org_select=org_select)

    def update(self, old_name, orgs, new_orgs, new_name=None,
               org_select=False):
        """
        Updates an environment.
        """
        element = self.search(old_name)
        if element:
            element.click()
            if self.wait_until_element(locators["env.name"]) and new_name:
                self.field_update("env.name", new_name)
            self._configure_env(orgs, new_orgs=new_orgs,
                                org_select=org_select)

    def search(self, name):
        """
        Searches existing env from UI
        """
        element = self.search_entity(name,
                                     locators["env.env_name"])
        return element

    def delete(self, name, really):
        """
        Deletes the environment.
        """

        self.delete_entity(name, really, locators["env.env_name"],
                           locators['env.delete'],
                           drop_locator=locators["env.dropdown"])
