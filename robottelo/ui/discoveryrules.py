# -*- encoding: utf-8 -*-
"""Implements Discovery Rules from UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class DiscoveryRules(Base):
    """Manipulates Discovery Rules from UI"""

    def create(self, name, search_rule, hostgroup, hostname=None,
               host_limit=None, priority=None, enabled=False):
        """Creates new discovery rule from UI"""
        self.wait_until_element(locators['discoveryrules.new']).click()
        self.wait_for_ajax()
        if not self.wait_until_element(locators['discoveryrules.name']):
            raise UIError(u'Could not create new discovery "{0}"'.format(name))
        self.text_field_update(locators['discoveryrules.name'], name)
        self.wait_for_ajax()
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
            self.find_element(locators['discoveryrules.enabled']).click()
        self.wait_until_element(common_locators['submit']).click()
        self.wait_for_ajax()

    def search(self, rule_name):
        """Searches existing discovery rule from UI"""
        self.wait_for_ajax()
        Navigator(self.browser).go_to_discovery_rules()
        strategy, value = locators['discoveryrules.rule_name']
        element = self.wait_until_element((strategy, value % rule_name))
        return element

    def delete(self, rule_name, really=True):
        """Delete existing discovery rule from UI"""
        Navigator(self.browser).go_to_discovery_rules()
        strategy, value = locators['discoveryrules.rule_delete']
        self.wait_until_element((strategy, value % rule_name)).click()
        self.handle_alert(really)
