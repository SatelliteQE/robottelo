# -*- encoding: utf-8 -*-
"""Implements Bookmarks UI"""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Bookmark(Base):
    """Implements CRUD functions for UI"""

    def navigate_to_entity(self):
        """Navigate to Bookmark entity page"""
        Navigator(self.browser).go_to_bookmarks()

    def _search_locator(self):
        """Specify locator for Bookmark entity search procedure"""
        return locators['bookmark.select_name']

    def update(self, name, new_name=None, new_query=None,
               new_public=None, search_query=None):
        """Updates a bookmark."""
        self.click(self.search(name, _raw_query=search_query))
        self.wait_until_element(locators['bookmark.name'])
        if new_name is not None:
            self.assign_value(locators['bookmark.name'], new_name)
        if new_query is not None:
            self.assign_value(locators['bookmark.query'], new_query)
        if new_public is not None:
            self.assign_value(locators['bookmark.public'], new_public)
        self.click(common_locators['submit'])

    def validate_field(self, name, field_name, expected_value,
                       search_query=None):
        """Check that bookmark field has expected value"""
        bm_element = self.search(name, _raw_query=search_query)
        self.click(bm_element)
        if field_name in ['name', 'query']:
            return (
                self.wait_until_element(locators['bookmark.' + field_name])
                .get_attribute('value') == expected_value
            )
        elif field_name == 'public':
            return (
                self.wait_until_element(locators['bookmark.' + field_name])
                .is_selected() == expected_value
            )
        return False
