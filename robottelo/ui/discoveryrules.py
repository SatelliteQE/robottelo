# -*- encoding: utf-8 -*-
"""Implements Discovery Rules from UI."""
from robottelo.constants import FILTER
from robottelo.decorators import affected_by_bz
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class DiscoveryRules(Base):
    """Manipulates Discovery Rules from UI"""

    def _configure_discovery(self, hostname=None, host_limit=None,
                             priority=None, locations=None, organizations=None,
                             enabled=True):
        """Configures various parameters for discovery rule."""
        if hostname:
            self.assign_value(
                locators['discoveryrules.hostname'],
                hostname
            )
        if host_limit:
            self.assign_value(
                locators['discoveryrules.host_limit'],
                host_limit
            )
        if priority:
            self.assign_value(
                locators['discoveryrules.priority'],
                priority
            )
        self.assign_value(locators['discoveryrules.enabled'], enabled)
        if locations:
            self.configure_entity(
                locations,
                FILTER['discovery_rule_loc'],
                tab_locator=tab_locators['tab_loc'],
            )
        if organizations:
            self.configure_entity(
                organizations,
                FILTER['discovery_rule_org'],
                tab_locator=tab_locators['tab_org'],
            )

    def create(self, name, search_rule, hostgroup, hostname=None,
               host_limit=None, priority=None, locations=None,
               organizations=None, select=True, enabled=True):
        """Creates new discovery rule from UI"""
        self.click(locators['discoveryrules.new'])
        self.assign_value(locators['discoveryrules.name'], name)
        self.assign_value(locators['discoveryrules.search'], search_rule)
        self.assign_value(
            locators['discoveryrules.hostgroup_dropdown'], hostgroup)
        self._configure_discovery(
            hostname, host_limit, priority, locations, organizations)
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
        if not affected_by_bz(1233135):
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
            drop_locator=locators['discoveryrules.dropdown'],
        )

    def update(self, name, new_name=None, search_rule=None, hostgroup=None,
               hostname=None, host_limit=None, priority=None, enabled=True):
        """Update an existing discovery rule from UI."""
        self.search_and_click(name)
        if new_name is not None:
            self.assign_value(locators['discoveryrules.name'], new_name)
        if search_rule:
            self.assign_value(locators['discoveryrules.search'], search_rule)
        if hostgroup:
            self.assign_value(
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
        self.search_and_click(name)
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
