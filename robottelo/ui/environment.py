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

    def _configure_taxonomies(self, locations=None, organizations=None):
        """Associate role with organization or location"""
        if locations:
            self.configure_entity(
                locations,
                FILTER['env_loc'],
                tab_locator=tab_locators['tab_loc'],
            )
        if organizations:
            self.configure_entity(
                organizations,
                FILTER['env_org'],
                tab_locator=tab_locators['tab_org'],
            )

    def create(self, name, organizations, locations):
        """Creates the environment."""
        self.click(locators['env.new'])
        self.assign_value(locators['env.name'], name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])

    def update(
            self, old_name, new_name=None, locations=None, organizations=None):
        """Updates an environment."""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['env.name'], new_name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])
