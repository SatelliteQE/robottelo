# -*- encoding: utf-8 -*-
"""Implements Global Parameters ."""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class GlobalParameters(Base):
    """Provides the CRUD functionality for Global Parameters."""

    def navigate_to_entity(self):
        """Navigate to Global Parameters entity page"""
        Navigator(self.browser).go_to_global_parameters()

    def _search_locator(self):
        """Specify locator for Global Parameters entity search procedure"""
        return locators['globalparameters.select']

    def create(self, name, value=None, hidden_value=None):
        """Creates a Global Parameter"""
        self.click(locators['globalparameters.new'])
        self.assign_value(locators['globalparameters.name'], name)
        if value is not None:
            self.assign_value(locators['globalparameters.value'], value)
        if hidden_value is not None:
            self.assign_value(
                locators['globalparameters.hidden_value'], hidden_value)
        self.click(common_locators['submit'])

    def update(self, name, new_name=None, value=None, hidden_value=None):
        """Updates a Global Parameter"""
        self.search_and_click(name)
        if new_name is not None:
            self.assign_value(locators['globalparameters.name'], new_name)
        if value is not None:
            self.assign_value(locators['globalparameters.value'], value)
        if hidden_value is not None:
            self.assign_value(
                locators['globalparameters.hidden_value'], hidden_value)
        self.click(common_locators['submit'])
