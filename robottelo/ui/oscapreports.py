# -*- encoding: utf-8 -*-
"""Implements Open Scap  Reports for UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class OpenScapReports(Base):
    """Manipulates OpenScap Reports from UI"""
    search_key = 'host'

    def navigate_to_entity(self):
        """Navigate to OpenScap Reports entity page"""
        Navigator(self.browser).go_to_oscap_reports()

    def _search_locator(self):
        """Specify locator for OpenScap Reports entity search procedure"""
        return locators['oscap.report_select']
