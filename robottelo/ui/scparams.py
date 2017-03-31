# -*- encoding: utf-8 -*-
"""Implements Smart Class Parameters UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class SmartClassParameter(Base):
    """Manipulates Smart class parameters from UI"""

    search_key = 'parameter'

    def navigate_to_entity(self):
        """Navigate to Smart class parameters entity page"""
        Navigator(self.browser).go_to_smart_class_parameters()

    def _search_locator(self):
        """Specify locator for Smart class parameters entity search
        procedure
        """
        return locators['sc_parameters.select_name']
