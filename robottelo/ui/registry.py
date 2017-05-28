# -*- encoding: utf-8 -*-
"""Implements Registry UI"""
from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Registry(Base):
    """Provides the CRUD functionality for Registry."""

    def navigate_to_entity(self):
        """Navigate to Registry entity page"""
        Navigator(self.browser).go_to_registries()

    def _search_locator(self):
        """Specify locator for Registry entity search procedure"""
        return locators['registry.select_name']

    def create(self, name, url, description=None, username=None, password=None,
               orgs=None, org_select=True, locs=None, loc_select=True):
        """Creates the registry."""
        self.click(locators['registry.new'])
        self.assign_value(locators['registry.name'], name)
        self.assign_value(locators['registry.url'], url)
        if description:
            self.assign_value(locators['registry.description'], description)
        if username:
            self.assign_value(locators['registry.username'], username)
        if password:
            self.assign_value(locators['registry.password'], password)
        if orgs:
            self.configure_entity(
                orgs,
                FILTER['reg_org'],
                tab_locator=tab_locators['tab_org'],
                entity_select=org_select,
            )
        if locs:
            self.configure_entity(
                locs,
                FILTER['reg_loc'],
                tab_locator=tab_locators['tab_loc'],
                entity_select=loc_select,
            )
        self.click(common_locators['submit'])

    def update(self, name, new_name=None, new_url=None, new_desc=None,
               new_username=None, new_pass=None, orgs=None, new_orgs=None,
               org_select=False, locs=None, new_locs=None, loc_select=False):
        """Updates a registry."""
        self.search_and_click(name)
        if new_name:
            self.assign_value(locators['registry.name'], new_name)
        if new_url:
            self.assign_value(locators['registry.url'], new_url)
        if new_desc:
            self.assign_value(locators['registry.description'], new_desc)
        if new_username:
            self.assign_value(locators['registry.username'], new_username)
        if new_pass:
            self.assign_value(locators['registry.password'], new_pass)
        self.configure_entity(
            orgs,
            FILTER['reg_org'],
            tab_locator=tab_locators['tab_org'],
            new_entity_list=new_orgs,
            entity_select=org_select,
        )
        self.configure_entity(
            locs,
            FILTER['reg_loc'],
            tab_locator=tab_locators['tab_loc'],
            new_entity_list=new_locs,
            entity_select=loc_select,
        )
        self.click(common_locators['submit'])
