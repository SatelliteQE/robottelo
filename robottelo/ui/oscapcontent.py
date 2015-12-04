# -*- encoding: utf-8 -*-
"""Implements Open Scap  Content for UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, tab_locators, common_locators
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

    def create(self, name, content_path=None):
        """Creates new oscap Content from UI"""
        self.click(locators['oscap.upload_content'])
        if not self.wait_until_element(locators['oscap.content_title']):
            raise UIError(
                u'Could not create new Oscap Content {0}'
                .format(name)
            )
        self.text_field_update(locators['oscap.content_title'], name)
        self.wait_until_element(
            locators['oscap.content_path']
        ).send_keys(content_path)
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
        strategy, value = locators['oscap.content_edit']
        self.click((strategy, value % name))
        if content_org:
            self.click(tab_locators['tab_org'])
            self.configure_entity([content_org], FILTER['oscap_org'])
        self.click(common_locators['submit'])
