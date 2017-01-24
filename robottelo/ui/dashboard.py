# -*- encoding: utf-8 -*-
"""Implements Dashboard UI"""

from robottelo.helpers import escape_search
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Dashboard(Base):
    """Manipulates dashboard from UI"""

    def navigate_to_entity(self):
        """Navigate to Dashboard entity page"""
        Navigator(self.browser).go_to_dashboard()

    def _search_locator(self):
        """Specify locator for Dashboard entity search procedure"""
        # There is no element that can be clicked or directly and logically
        # associated with Dashboard entity. Total hosts count returned by
        # search seems the most closer fact to our ideology
        return locators['dashboard.hosts_total']

    def search(self, name, search_key=None):
        """Perform search on Dashboard page and return hosts count found"""
        if search_key is None:
            search_string = name
        else:
            search_string = u'{0} = {1}'.format(
                search_key, escape_search(name))
        self.assign_value(common_locators['search'], search_string)
        self.click(common_locators['search_button'])
        _, count = self.wait_until_element(
            self._search_locator()).text.split(': ')
        return count
