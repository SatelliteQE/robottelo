# -*- encoding: utf-8 -*-
"""Implements Tasks UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Task(Base):
    """Provides the basic functionality for Tasks"""

    search_key = 'id'

    def navigate_to_entity(self):
        """Navigate to Tasks entity page"""
        Navigator(self.browser).go_to_tasks()

    def _search_locator(self):
        """Specify locator for Tasks entity search procedure"""
        return locators['task.select_name']
