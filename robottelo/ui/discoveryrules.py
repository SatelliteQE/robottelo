# -*- encoding: utf-8 -*-
"""Implements Discovery Rules from UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class DiscoveryRules(Base):
    """Manipulates Discovery Rules from UI"""

    def _configure_discovery(self, hostname=None, host_limit=None,
                             priority=None, enabled=False):
        """Configures various parameters for discovery rule."""
        if hostname:
            self.text_field_update(
                locators['discoveryrules.hostname'],
                hostname
            )
        if host_limit:
            self.text_field_update(
                locators['discoveryrules.host_limit'],
                host_limit
            )
        if priority:
            self.text_field_update(
                locators['discoveryrules.priority'],
                priority
            )
        if enabled:
            self.click(locators['discoveryrules.enabled'])

    def create(self, name, search_rule, hostgroup, hostname=None,
               host_limit=None, priority=None, enabled=False):
        """Creates new discovery rule from UI"""
        self.click(locators['discoveryrules.new'])
        if not self.wait_until_element(locators['discoveryrules.name']):
            raise UIError(u'Could not create new discovery "{0}"'.format(name))
        self.text_field_update(locators['discoveryrules.name'], name)
        if not search_rule:
            raise UIError(
                u'Could not create new discovery rule "{0}",'
                'without search_rule'.format(search_rule)
            )
        self.text_field_update(locators['discoveryrules.search'], search_rule)
        if not hostgroup:
            raise UIError(
                u'Could not create new discovery rule "{0}", without'
                'hostgroup'.format(search_rule)
            )
        Select(
            self.find_element(locators['discoveryrules.hostgroup'])
        ).select_by_visible_text(hostgroup)
        self._configure_discovery(hostname, host_limit, priority, enabled)
        self.click(common_locators['submit'])

    def search(self, rule_name):
        """Searches existing discovery rule from UI"""
        Navigator(self.browser).go_to_discovery_rules()
        strategy, value = locators['discoveryrules.rule_name']
        return self.wait_until_element((strategy, value % rule_name))

    def delete(self, rule_name, really=True):
        """Delete existing discovery rule from UI"""
        Navigator(self.browser).go_to_discovery_rules()
        strategy, value = locators['discoveryrules.rule_delete']
        self.click((strategy, value % rule_name), wait_for_ajax=False)
        self.handle_alert(really)

    def update(self, name, new_name=None, search_rule=None, hostgroup=None,
               hostname=None, host_limit=None, priority=None, enabled=False):
        """Update an existing discovery rule from UI."""
        element = self.search(name)
        if not element:
            raise UIError(
                'Could not update the discovery rule "{0}"'.format(name)
            )
        element.click()
        if new_name:
            if self.wait_until_element(locators['discoveryrules.name']):
                self.field_update('discoveryrules.name', new_name)
        if search_rule:
            if self.wait_until_element(locators['discoveryrules.search']):
                self.field_update('discoveryrules.search', search_rule)
        if hostgroup:
            Select(
                self.find_element(locators['discoveryrules.hostgroup'])
            ).select_by_visible_text(hostgroup)
        self._configure_discovery(hostname, host_limit, priority, enabled)
        self.click(common_locators['submit'])
