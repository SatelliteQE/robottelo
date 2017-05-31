# -*- encoding: utf-8 -*-
"""Implements Environment UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Environment(Base):
    """Provides the CRUD functionality for Environment."""

    def navigate_to_entity(self):
        """Navigate to Environment entity page"""
        Navigator(self.browser).go_to_environments()

    def _search_locator(self):
        """Specify locator for Environment entity search procedure"""
        return locators['env.env_name']

    def create(self, name, orgs, org_select=True):
        """Creates the environment."""
        self.click(locators['env.new'])
        self.assign_value(locators['env.name'], name)
        if orgs:
            self.configure_entity(
                orgs,
                FILTER['env_org'],
                tab_locator=tab_locators['tab_org'],
                entity_select=org_select,
                )
        self.click(common_locators['submit'])

    def update(self, old_name, orgs=None, new_orgs=None, new_name=None,
               org_select=False):
        """Updates an environment."""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['env.name'], new_name)
        self.configure_entity(
            orgs,
            FILTER['env_org'],
            tab_locator=tab_locators['tab_org'],
            new_entity_list=new_orgs,
            entity_select=org_select
        )
        self.click(common_locators['submit'])
