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

    def delete(self, name, really=True):
        """Unregisters and completely deletes content host. Custom helper is
        needed as deletion works through unregistering menu, by selecting
        appropriate radio button."""
        self.logger.debug(u'Deleting entity %s', name)
        self.click(self.search(name))
        self.click(locators['contenthost.unregister'])
        self.click(locators['contenthost.confirm_deletion'])
        if really:
            self.click(common_locators['confirm_remove'])
        else:
            self.click(common_locators['cancel'])
        # Make sure that element is really removed from UI
        self.button_timeout = 3
        self.result_timeout = 1
        try:
            for _ in range(3):
                searched = self.search(name)
                if bool(searched) != really:
                    break
                self.browser.refresh()
            if bool(searched) == really:
                raise UIError(
                    u'Delete functionality works improperly for "{0}" entity'
                    .format(name))
        finally:
            self.button_timeout = 15
            self.result_timeout = 15

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

    def execute_package_action(self, name, action_name, action_value,
                               timeout=120):
        """Execute remote package action on a content host

        :param name: content host name to remotely execute package action on
        :param action_name: remote action to execute. Can be one of 5: 'Package
            Install', 'Package Update', 'Package Remove', 'Group Install' or
            'Group Remove'
        :param action_value: Package or package group group name to remotely
            install/upgrade/remove (depending on `action_name`)
        :param timeout: Timeout in seconds for remote action task to finish
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """
        self.click(self.search(name))
        self.click(tab_locators['contenthost.tab_packages'])
        self.assign_value(
            locators['contenthost.remote_actions'], action_name)
        self.assign_value(
            locators['contenthost.package_name_input'], action_value)
        self.click(locators['contenthost.perform_remote_action'])
        result = self.wait_until_element(
            locators['contenthost.remote_action_finished'],
            timeout=timeout,
        )
        if result is None:
            raise UIError('Timeout waiting for package action to finish')
        return result.get_attribute('type')

    def install_errata(self, name, errata_id, timeout=120):
        """Install errata on a content host

        :param name: content host name to apply errata on
        :param errata_id: errata id, e.g. 'RHEA-2012:0055'
        :param timeout: Timeout in seconds for errata installation task to
            finish
        :raise: UIError if remote task finished by timeout

        :return: Returns a string containing task status
        """
        self.click(self.search(name))
        self.click(tab_locators['contenthost.tab_errata'])
        strategy, value = locators['contenthost.errata_select']
        self.click((strategy, value % errata_id))
        self.click(locators['contenthost.errata_apply'])
        self.click(locators['contenthost.confirm_errata'])
        result = self.wait_until_element(
            locators['contenthost.remote_action_finished'],
            timeout=timeout,
        )
        if result is None:
            raise UIError('Timeout waiting for errata installation to finish')
        return result.get_attribute('type')

    def package_search(self, name, package_name):
        """Search for installed package on specific content host"""
        self.click(self.search(name))
        self.click(tab_locators['contenthost.tab_packages'])
        self.wait_until_element(locators['contenthost.package_search_box'])
        self.assign_value(
            locators['contenthost.package_search_box'], package_name)
        self.click(locators['contenthost.package_search_button'])
        strategy, value = locators['contenthost.package_search_name']
        return self.wait_until_element((strategy, value % package_name))

    def fetch_parameters(self, name, parameters_list):
        """Fetches parameter values of specified host

        :param name: content host's name (with domain)
        :param parameters_list: A list of parameters to be fetched. Each
            parameter should be a separate list containing tab name and
            parameter name in absolute correspondence to UI (Similar to
            parameters list passed to create a host). Example::

                [
                    ['Details', 'Registered By'],
                    ['Provisioning Details', 'Status'],
                ]

        :return: Dictionary of parameter name - parameter value pairs
        :rtype: dict
        """
        self.search_and_click(name)
        result = {}
        for tab_name, param_name in parameters_list:
            tab_locator = tab_locators['.tab_'.join((
                'contenthost',
                (tab_name.lower()).replace(' ', '_')
            ))]
            param_locator = locators['.fetch_'.join((
                'contenthost',
                (param_name.lower()).replace(' ', '_')
            ))]
            self.click(tab_locator)
            result[param_name] = self.wait_until_element(param_locator).text
        return result
