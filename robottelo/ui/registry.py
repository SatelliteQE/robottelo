# -*- encoding: utf-8 -*-
"""Implements Registry UI"""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Registry(Base):
    """Provides the CRUD functionality for Registry."""

    def create(self, name, url, description=None, username=None, password=None,
               orgs=None, org_select=True, locs=None, loc_select=True):
        """Creates the registry."""
        self.click(locators['registry.new'])
        self.text_field_update(locators['registry.name'], name)
        self.text_field_update(locators['registry.url'], url)
        if description:
            self.text_field_update(
                locators['registry.description'], description)
        if username:
            self.text_field_update(locators['registry.username'], username)
        if password:
            self.text_field_update(locators['registry.password'], password)
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
        element = self.search(name)
        if not element:
            raise UIError(
                'Could not find necessary registry "{0}"'.format(name)
            )
        element.click()
        if new_name:
            self.text_field_update(locators['registry.name'], new_name)
        if new_url:
            self.text_field_update(locators['registry.url'], new_url)
        if new_desc:
            self.text_field_update(locators['registry.description'], new_desc)
        if new_username:
            self.text_field_update(locators['registry.username'], new_username)
        if new_pass:
            self.text_field_update(locators['registry.password'], new_pass)
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

    def search(self, name):
        """Searches existing registry from UI"""
        Navigator(self.browser).go_to_registries()
        if len(name) <= 30:
            element = self.search_entity(
                name, locators['registry.select_name'])
        else:
            element = self.search_entity(
                name, common_locators['select_filtered_entity'])
        return element

    def delete(self, name, really=True):
        """Deletes the registry"""
        if len(name) <= 30:
            loc = locators['registry.select_name']
        else:
            loc = common_locators['select_filtered_entity']

        self.delete_entity(
            name,
            really,
            loc,
            locators['registry.delete'],
        )
