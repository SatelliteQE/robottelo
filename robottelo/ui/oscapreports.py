# -*- encoding: utf-8 -*-
"""Implements Open Scap  Reports for UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class OpenScapReports(Base):
    """Manipulates OpenScap Reports from UI"""

    def search(self, name):
        """Searches existing oscap reports from UI"""
        self.wait_for_ajax()
        Navigator(self.browser).go_to_oscap_reports()
        return self.search_entity(
            name,
            locators['oscap.report_select'],
            search_key='host',
        )

    def delete(self, name, really=True):
        """Delete existing oscap reports from UI"""
        Navigator(self.browser).go_to_oscap_reports()
        strategy, value = locators['oscap.report_delete']
        self.click((strategy, value % name))
        self.handle_alert(really)
