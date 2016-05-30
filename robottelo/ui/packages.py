# -*- encoding: utf-8 -*-
"""Implements Packages UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Package(Base):
    """Manipulates Packages from UI"""

    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Package entity page"""
        Navigator(self.browser).go_to_packages()

    def _search_locator(self):
        """Specify locator for Package entity search procedure"""
        return locators['package.rpm_name']
