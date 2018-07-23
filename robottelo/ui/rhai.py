# -*- encoding: utf-8 -*-
""" Implements methods for RHAI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class AccessInsightsError(Exception):
    """Exception raised for failed Access Insights configuration operations"""


class RHAIInventory(Base):
    """Implements functionality for RHAI Inventory."""

    def navigate_to_entity(self):
        """Navigate to RHAI Inventory page"""
        Navigator(self.browser).go_to_insights_inventory()

    def _search_locator(self):
        """Specify locator for system entity search procedure"""
        return locators['insight.inventory.system']

    def search(self, element_name):
        """Search for system with element name"""
        self.navigate_to_entity()
        self.assign_value(locators['insight.inventory.search'], element_name)
        # the search here has no summit button, a change event is triggered
        # when we push characters in search box
        return self.wait_until_element(self._search_locator() % element_name)

    def get_total_systems(self):
        """To get the number of registered systems.

        :return a string that looks like: "0 Systems" or "1 System" etc...
        """
        self.navigate_to_entity()
        return self.wait_until_element(
            locators['insights.registered_systems']).text

    def unregister_system(self, system_name):
        """Unregister system from inventory"""
        system_element = self.search(system_name)
        if system_element is None:
            raise UIError('system "{0}" not found'.format(system_name))
        self.assign_value(
            locators["insight.inventory.system_checkbox"] % system_name,
            True
        )
        self.click(locators["insight.inventory.actions_button"])
        self.click(locators["insight.inventory.action_unregister"])
        self.click(locators["insight.inventory.action_confirm_yes"])


class RHAIOverview(Base):
    """Implements functionality for RHAI Overview."""

    def navigate_to_entity(self):
        """Navigate to RHAI Overview page"""
        Navigator(self.browser).go_to_insights_overview()

    def get_organization_selection_message(self):
        """Return the organization selection message text if exist"""
        self.navigate_to_entity()
        msg_element = self.wait_until_element(
            locators['insights.org_selection_msg'])
        if msg_element is not None:
            return msg_element.text
        return None


class RHAIManage(Base):
    """Implements functionality for RHAI Manage."""

    def navigate_to_entity(self):
        """Navigate to RHAI Manage page"""
        Navigator(self.browser).go_to_insights_manage()

    @property
    def is_service_enabled(self):
        self.navigate_to_entity()
        checkbox = self.wait_until_element(
            locators['insights.manage.service_status'])
        classes = checkbox.get_attribute("class").split()
        return 'ng-not-empty' in classes

    def _switch_service(self, enable):
        if (self.is_service_enabled and not enable or
                not self.is_service_enabled and enable):
                self.click(locators['insights.manage.service_status'])
                self.click(locators['insights.manage.save_status'])

    def enable_service(self):
        self._switch_service(True)

    def disable_service(self):
        self._switch_service(False)

    @property
    def is_insights_engine_connected(self):
        self.navigate_to_entity()
        label = self.wait_until_element(
            locators['insights.manage.connection_status'])
        return label.text == 'Connected'

    @property
    def account_number(self):
        self.navigate_to_entity()
        label = self.wait_until_element(
            locators['insights.manage.account_number'])
        return label.text

    def check_connection(self):
        self.navigate_to_entity()
        self.click(locators['insights.manage.service_status'])
