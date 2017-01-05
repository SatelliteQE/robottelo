# -*- encoding: utf-8 -*-
"""Implements Open Scap  Content for UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class OpenScapContent(Base):
    """Manipulates OpenScap content from UI"""
    search_key = 'title'

    def navigate_to_entity(self):
        """Navigate to OpenScap content entity page"""
        Navigator(self.browser).go_to_oscap_content()

    def _search_locator(self):
        """Specify locator for OpenScap content entity search procedure"""
        return locators['oscap.content_select']

    def create(self, name, content_path=None,
               content_org=None, content_loc=None):
        """Creates new oscap Content from UI"""
        self.click(locators['oscap.upload_content'])
        self.assign_value(locators['oscap.content_title'], name)
        self.assign_value(locators['oscap.content_path'], content_path)
        if content_org:
            self.click(tab_locators['tab_org'])
            self.configure_entity([content_org], FILTER['oscap_org'])
        if content_loc:
            self.click(tab_locators['tab_loc'])
            self.configure_entity([content_org], FILTER['oscap_loc'])
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Delete existing oscap content from UI"""
        self.delete_entity(
            name,
            really,
            locators['oscap.content_delete'],
            drop_locator=locators['oscap.content_dropdown'],
        )

    def update(self, name, new_name=None, content_org=None, content_loc=None):
        """Updates existing oscap content from UI"""
        element = self.search(name)
        if not element:
            raise UIError(u'Could not find oscap content {0}'.format(name))
        self.click(locators['oscap.content_edit'] % name)
        if content_org:
            self.click(tab_locators['tab_org'])
            self.configure_entity([content_org], FILTER['oscap_org'])
        self.click(common_locators['submit'])
