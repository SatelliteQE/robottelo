# -*- encoding: utf-8 -*-
"""Implements Open Scap  Tailoring File for UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class OpenScapTailoringfile(Base):
    """Manipulates OpenScap Tailoring File from UI"""
    search_key = 'name'
    actions_dropdown_locator = locators['oscap.content_dropdown']

    def navigate_to_entity(self):
        """Navigate to OpenScap Tailoring File entity page"""
        Navigator(self.browser).go_to_oscap_tailoringfile()

    def _search_locator(self):
        """Specify locator for Tailoring File entity search procedure"""
        return locators['oscap.content_select']

    def create(self, name, tailoring_path=None,
               tailoring_org=None, tailoring_loc=None):
        """Creates new oscap Tailoring File from UI"""
        self.click(locators['oscap.upload_tailoringfile'])
        self.assign_value(locators['oscap.tailoringfile_title'], name)
        self.assign_value(locators['oscap.tailoringfile_path'], tailoring_path)
        if tailoring_org:
            self.click(tab_locators['tab_org'])
            self.configure_entity([tailoring_org],
                                  FILTER['oscap_tailoring_org'])
        if tailoring_loc:
            self.click(tab_locators['tab_loc'])
            self.configure_entity([tailoring_loc],
                                  FILTER['oscap_tailoring_loc'])
        self.click(common_locators['submit'])
