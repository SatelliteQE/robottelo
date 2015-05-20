# -*- encoding: utf-8 -*-
"""
Implements Monitor->Trends UI
"""

from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Trend(Base):
    """Provides the CRUD functionality for Trends."""

    def create(self, trend_type, trendable, name):
        """Creates the trend."""
        self.wait_until_element(locators['trend.new']).click()

        if self.wait_until_element(locators['trend.type']):
            Select(
                self.find_element(locators['trend.type'])
            ).select_by_visible_text(trend_type)

            if trendable is not None:
                Select(
                    self.find_element(locators['trend.trendable'])
                ).select_by_visible_text(trendable)

            if name is not None and trendable is not None:
                self.find_element(locators['trend.name']).send_keys(name)

        self.find_element(common_locators['submit']).click()
        self.wait_for_ajax()

    def update(self, trend_name, entity_name, entity_value):
        """Updates a trend."""
        element = self.search(trend_name)
        if element is None:
            raise UIError(
                'Could not find necessary trend "{0}"'.format(trend_name)
            )
        strategy = locators['trend.edit'][0]
        value = locators['trend.edit'][1]
        edit_fld = self.wait_until_element((strategy, value % trend_name))
        edit_fld.click()
        strategy = locators['trend.edit_entity'][0]
        value = locators['trend.edit_entity'][1]
        txt_fld = self.wait_until_element((strategy, value % entity_name))
        if txt_fld is None:
            raise UINoSuchElementError(
                u'Could not find the entity "{0}" for update procedure.'
                .format(entity_name)
            )
        txt_fld.clear()
        txt_fld.send_keys(entity_value)
        self.find_element(common_locators['submit']).click()
        self.wait_for_ajax()

    def search(self, tr_type):
        """Searches existing trend from UI

        As we do not have search field for trend UI screen, so it is impossible
        to re-use search functionality that was used for all application
        testing logic.

        """
        Navigator(self.browser).go_to_trends()
        strategy = locators['trend.trend_name'][0]
        value = locators['trend.trend_name'][1]
        element = self.wait_until_element((strategy, value % tr_type))
        return element

    def delete(self, trend_name, really):
        """Deletes the trend."""
        element = self.search(trend_name)
        if element is None:
            raise UIError(
                'Could not find necessary trend "{0}"'.format(trend_name)
            )
        strategy = locators['trend.dropdown'][0]
        value = locators['trend.dropdown'][1]
        dropdown = self.wait_until_element((strategy, value % trend_name))
        if dropdown is None:
            raise UINoSuchElementError(
                u'Could not select the entity "{0}" for deletion.'
                .format(trend_name)
            )
        dropdown.click()
        strategy = locators['trend.delete'][0]
        value = locators['trend.delete'][1]
        self.wait_until_element((strategy, value % trend_name)).click()
        self.handle_alert(really)
