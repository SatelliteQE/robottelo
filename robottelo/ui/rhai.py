# -*- encoding: utf-8 -*-
""" Implements methods for RHAI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class AccessInsightsError(Exception):
    """Exception raised for failed Access Insights configuration operations"""


class RHAI(Base):
    def view_registered_systems(self):
        """To view the number of registered systems"""
        result = self.wait_until_element(
            locators['insights.registered_systems']
        ).text
        return result

    def unregister_system_from_inventory(self, system_name, confirm=True):
        """Unregister system from inventory"""
        Navigator(self.browser).go_to_insights_inventory()
        # select the system
        self.assign_value(
            locators["insight.inventory.system_checkbox"] % system_name,
            True
        )
        # click on drop-down actions button
        self.click(locators["insight.inventory.actions_button"])
        # click on unregister action
        self.click(locators["insight.inventory.action_unregister"])
        if confirm:
            # click on yes dialog button
            self.click(locators["insight.inventory.action_confirm_yes"])
