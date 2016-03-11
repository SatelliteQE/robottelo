# -*- encoding: utf-8 -*-
"""Implements Discovery Rules from UI."""
from robottelo.decorators import bz_bug_is_open
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class DiscoveryRules(Base):
    """Manipulates Discovery Rules from UI"""

    def _configure_discovery(self, hostname=None, host_limit=None,
                             priority=None, enabled=True):
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
        self.assign_value(locators['discoveryrules.enabled'], enabled)

    def create(self, name, search_rule, hostgroup, hostname=None,
               host_limit=None, priority=None, enabled=True):
        """Creates new discovery rule from UI"""
        self.click(locators['discoveryrules.new'])
        if not self.wait_until_element(locators['discoveryrules.name']):
            raise UIError(u'Could not create new discovery "{0}"'.format(name))
        self.text_field_update(locators['discoveryrules.name'], name)
        self.text_field_update(locators['discoveryrules.search'], search_rule)
        self.select(locators['discoveryrules.hostgroup_dropdown'], hostgroup)
        self._configure_discovery(hostname, host_limit, priority, enabled)
        self.click(common_locators['submit'])

    def navigate_to_entity(self):
        """Navigate to Discovery Rule entity page"""
        Navigator(self.browser).go_to_discovery_rules()

    def _search_locator(self):
        """Specify locator for Discovery Rule entity search procedure"""
        return locators['discoveryrules.rule_name']

    def search(self, name):
        """Searches existing discovery rule from UI. It is necessary to use
        custom search as we don't have both search bar and search button there.
        """
        if not bz_bug_is_open(1233135):
            raise DeprecationWarning(
                'Search box is implemented. Use generic search method'
            )
        self.navigate_to_entity()
        strategy, value = self._search_locator()
        if len(name) > 32:
            strategy, value = common_locators['select_filtered_entity']
        return self.wait_until_element((strategy, value % name))

    def delete(self, name, really=True):
        """Delete existing discovery rule from UI"""
        self.delete_entity(
            name,
            really,
            locators['discoveryrules.rule_delete'],
        )

    def update(self, name, new_name=None, search_rule=None, hostgroup=None,
               hostname=None, host_limit=None, priority=None, enabled=True):
        """Update an existing discovery rule from UI."""
        element = self.search(name)
        self.click(element)
        if new_name is not None:
            if self.wait_until_element(locators['discoveryrules.name']):
                self.field_update('discoveryrules.name', new_name)
        if search_rule:
            if self.wait_until_element(locators['discoveryrules.search']):
                self.field_update('discoveryrules.search', search_rule)
        if hostgroup:
            self.select(
                locators['discoveryrules.hostgroup_dropdown'], hostgroup)
        self._configure_discovery(hostname, host_limit, priority, enabled)
        self.click(common_locators['submit'])

    def get_attribute_value(self, name, attribute_name, element_type='field'):
        """Get corresponding Discovery Rule attribute value

        :param str name: Discovery Rule name
        :param str attribute_name: Discovery Rule attribute to be read
            (supported attributes: 'search', 'hostgroup', 'hostname',
            'host_limit', 'priority', 'enabled')
        :param str element_type: Specify expected type of attribute to be read
            (supported types: 'field', 'select' and 'checkbox')
        :return str result: Return attribute value to be asserted further on
            the test level

        """
        discovery_rule = self.search(name)
        self.click(discovery_rule)
        element = self.wait_until_element(
            locators['discoveryrules.{0}'.format(attribute_name)])
        if element_type == 'field':
            result = element.get_attribute('value')
        elif element_type == 'select':
            result = element.text
        elif element_type == 'checkbox':
            result = element.is_selected()
        else:
            raise ValueError(
                u'"{0}" type is not currently supported.'.format(element_type))
        return result
