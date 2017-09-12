# -*- encoding: utf-8 -*-
"""Implements Monitor->Statistics UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Statistic(Base):
    """Provides basic functionality for Statistics page"""

    def navigate_to_entity(self):
        """Navigate to Statistics entity page"""
        Navigator(self.browser).go_to_statistics()

    def _search_locator(self):
        """There are no search functionality for Statistic page"""
        return None

    def get_chart_title_data(self, chart_name):
        """Get title information that located inside of the chart"""
        self.navigate_to_entity()
        title_text = self.wait_until_element(
            locators['statistic.chart_title_text'] % chart_name).text
        title_value = self.wait_until_element(
            locators['statistic.chart_title_value'] % chart_name).text
        return {'text': title_text, 'value': title_value}
