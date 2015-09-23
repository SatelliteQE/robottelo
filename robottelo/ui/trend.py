# -*- encoding: utf-8 -*-
"""Implements Monitor->Trends UI"""

from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Trend(Base):
    """Provides the CRUD functionality for Trends."""

    def create(self, trend_type, trendable, name):
        """Creates the trend."""
        self.click(locators['trend.new'])

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

        self.click(common_locators['submit'])

    def update(self, trend_name, entity_name, entity_value):
        """Updates a trend."""
        element = self.search(trend_name)
        if element is None:
            raise UIError(
                'Could not find necessary trend "{0}"'.format(trend_name)
            )
        strategy, value = locators['trend.edit']
        self.click((strategy, value % trend_name))
        strategy, value = locators['trend.edit_entity']
        txt_fld = self.wait_until_element((strategy, value % entity_name))
        if txt_fld is None:
            raise UINoSuchElementError(
                u'Could not find the entity "{0}" for update procedure.'
                .format(entity_name)
            )
        txt_fld.clear()
        txt_fld.send_keys(entity_value)
        self.click(common_locators['submit'])

    def search(self, tr_type):
        """Searches existing trend from UI

        As we do not have search field for trend UI screen, so it is impossible
        to re-use search functionality that was used for all application
        testing logic.

        """
        Navigator(self.browser).go_to_trends()
        strategy, value = locators['trend.trend_name']
        return self.wait_until_element((strategy, value % tr_type))

    def delete(self, trend_name, really=True):
        """Deletes the trend."""
        element = self.search(trend_name)
        if element is None:
            raise UIError(
                'Could not find necessary trend "{0}"'.format(trend_name)
            )
        strategy, value = locators['trend.dropdown']
        self.click((strategy, value % trend_name))
        strategy, value = locators['trend.delete']
        self.click((strategy, value % trend_name), wait_for_ajax=False)
        self.handle_alert(really)
