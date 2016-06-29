"""Utilities to manipulate content hosts via UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class ContentHost(Base):
    """Manipulates Content Hosts from UI"""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Content Hosts entity page"""
        Navigator(self.browser).go_to_content_hosts()

    def _search_locator(self):
        """Specify locator for Content Hosts entity search procedure"""
        return locators['contenthost.select_name']

    def add_subscriptions(self, subscriptions=None, tab_locator=None,
                          select_locator=None):
        """Add or remove subscription association for content host."""
        strategy, value = locators['contenthost.subscription_select']
        self.click(tab_locators['contenthost.tab_subscriptions'])
        self.click(tab_locators['contenthost.tab_subscriptions_subscriptions'])
        if not self.wait_until_element(tab_locator):
            raise UIError('Can not manage subscriptions for content host.'
                          'Make sure content host is registered')
        self.click(tab_locators['contenthost.add_subscription'])
        for subscription in subscriptions:
            self.click(strategy, value % subscription)
        self.click(select_locator)

    def update(self, name, new_name=None, add_subscriptions=None,
               rm_subscriptions=None):
        """Updates an existing content host"""
        self.click(self.search(name))
        self.click(tab_locators['contenthost.tab_details'])

        if new_name:
            self.edit_entity(
                locators['contenthost.edit_name'],
                locators['contenthost.edit_name_text'],
                new_name,
                locators['contenthost.save_name'],
            )
        if add_subscriptions:
            self.add_subscriptions(
                subscriptions=add_subscriptions,
                tab_locator=tab_locators['contenthost.add_subscription'],
                select_locator=locators['contenthost.add_selected'],
            )
        if rm_subscriptions:
            self.add_subscriptions(
                subscriptions=add_subscriptions,
                tab_locator=tab_locators['contenthost.list_subscriptions'],
                select_locator=locators['contenthost.remove_selected'],
            )

    def unregister(self, name, really=True):
        """Unregisters a content host."""
        self.click(self.search(name))
        self.click(locators['contenthost.unregister'])
        if really:
            self.click(common_locators['confirm_remove'])
        else:
            self.click(common_locators['cancel'])

    def validate_subscription_status(self, name, expected_value=True,
                                     timeout=120):
        """Check whether a content host has active subscription or not"""
        for _ in range(timeout / 5):
            self.search(name)
            strategy, value = (
                locators['contenthost.subscription_active'] if expected_value
                else locators['contenthost.subscription_not_active']
            )
            result = self.wait_until_element(
                (strategy, value % name), timeout=5)
            if result:
                return True
        return False

    def install_package(self, name, package_name):
        """Remotely install package to content host"""
        self.click(self.search(name))
        self.click(tab_locators['contenthost.tab_packages'])
        self.assign_value(
            locators['contenthost.remote_actions'], 'Package Install')
        self.assign_value(
            locators['contenthost.package_name_input'], package_name)
        self.click(locators['contenthost.perform_remote_action'])
