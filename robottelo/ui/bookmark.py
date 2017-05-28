# -*- encoding: utf-8 -*-
"""Implements Bookmarks UI"""
from robottelo.decorators import bz_bug_is_open
from robottelo.ui.base import Base, UIError
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

    def update(self, controller, name, new_name=None, new_query=None,
               new_public=None):
        """Updates a bookmark."""
        element = self.search(controller, name)
        self.click(element)
        self.wait_until_element(locators['bookmark.name'])
        if new_name is not None:
            self.assign_value(locators['bookmark.name'], new_name)
        if new_query is not None:
            self.assign_value(locators['bookmark.query'], new_query)
        if new_public is not None:
            self.assign_value(locators['bookmark.public'], new_public)
        self.click(common_locators['submit'])

    def search(self, controller, name):
        """Searches for existing bookmark via UI

        It is necessary to use a custom search as we don't have both search bar
        and search button there. Also bookmark names are unique only inside the
        same controller, so controller name should be specified too.
        """
        if not bz_bug_is_open(1322012):
            raise DeprecationWarning(
                'Search box is implemented. Use generic search method'
            )
        self.navigate_to_entity()
        strategy, value = (
            self._search_locator()
            if len(name) <= 32
            else locators['bookmark.select_long_name']
        )
        return self.wait_until_element((strategy, value % (controller, name)))

    def delete(self, controller, name, really=True):
        """Deletes a bookmark."""
        searched = self.search(controller, name)
        if not searched:
            raise UIError(u'Could not find the bookmark "{0}"'.format(name))
        self.click(
            common_locators['delete_button'] % name, wait_for_ajax=False)
        self.handle_alert(really)
        # Verify the bookmark was deleted
        for _ in range(3):
            searched = self.search(controller, name)
            if bool(searched) != really:
                break
            self.browser.refresh()
        if bool(searched) == really:
            raise UIError(
                u'Delete functionality works improperly for "{0}" bookmark'
                .format(name))

    def validate_field(self, controller, name, field_name, expected_value):
        """Check that bookmark field has expected value"""
        bm_element = self.search(controller, name)
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
