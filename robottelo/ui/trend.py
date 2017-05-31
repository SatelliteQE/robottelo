# -*- encoding: utf-8 -*-
"""Implements Monitor->Trends UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Trend(Base):
    """Provides the CRUD functionality for Trends."""

    def navigate_to_entity(self):
        """Navigate to Trend entity page"""
        Navigator(self.browser).go_to_trends()

    def _search_locator(self):
        """Specify locator for Trend entity search procedure"""
        return locators['trend.trend_name']

    def create(self, trend_type, trendable, name):
        """Creates the trend."""
        self.click(locators['trend.new'])

        if self.wait_until_element(locators['trend.type']):
            self.select(locators['trend.type'], trend_type)
            if trendable is not None:
                self.select(locators['trend.trendable'], trendable)
            if name is not None and trendable is not None:
                self.assign_value(locators['trend.name'], name)

        self.click(common_locators['submit'])

    def update(self, trend_name, entity_name, entity_value):
        """Updates a trend."""
        element = self.search(trend_name)
        if element is None:
            raise UIError(
                'Could not find necessary trend "{0}"'.format(trend_name)
            )
        self.click(locators['trend.edit'] % trend_name)
        self.assign_value(
            locators['trend.edit_entity'] % entity_name, entity_value)
        self.click(common_locators['submit'])

    def search(self, tr_type):
        """Searches existing trend from UI

        As we do not have search field for trend UI screen, so it is impossible
        to re-use search functionality that was used for all application
        testing logic.
        """
        self.navigate_to_entity()
        return self.wait_until_element(self._search_locator() % tr_type)
