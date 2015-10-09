# -*- encoding: utf-8 -*-
""" Implements methods for RHAI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators


class AccessInsightsError(Exception):
    """Exception raised for failed Access Insights configuration operations"""


class RHAI(Base):
    def view_registered_systems(self):
        """To view the number of registered systems"""
        result = self.wait_until_element(
            locators['insights.registered_systems']
        ).text
        return result
