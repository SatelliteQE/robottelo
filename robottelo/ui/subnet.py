# -*- encoding: utf-8 -*-
"""Implements Subnet UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Subnet(Base):
    """Provides the CRUD functionality for Subnet."""

    def navigate_to_entity(self):
        """Navigate to Subnet entity page"""
        Navigator(self.browser).go_to_subnets()

    def _search_locator(self):
        """Specify locator for Subnet entity search procedure"""
        return locators['subnet.display_name']

    def _configure_subnet(self, subnet_network, subnet_mask, domains=None,
                          subnet_gateway=None, subnet_primarydns=None,
                          subnet_secondarydns=None):
        """Configures the subnet."""
        if subnet_network:
            self.assign_value(locators['subnet.network'], subnet_network)
        if subnet_mask:
            self.assign_value(locators['subnet.mask'], subnet_mask)
        if subnet_gateway:
            self.assign_value(locators['subnet.gateway'], subnet_gateway)
        if subnet_primarydns:
            self.assign_value(
                locators['subnet.primarydns'], subnet_primarydns)
        if subnet_secondarydns:
            self.assign_value(
                locators['subnet.secondarydns'], subnet_secondarydns)
        if domains:
            self.configure_entity(
                domains,
                FILTER['sub_domain'],
                tab_locator=tab_locators['subnet.tab_domain']
            )

    def create(self, orgs, subnet_name=None, subnet_network=None,
               subnet_mask=None, subnet_gateway=None, subnet_primarydns=None,
               subnet_secondarydns=None, domains=None, org_select=True):
        """Create Subnet from UI"""
        self.click(locators['subnet.new'])
        self.assign_value(locators['subnet.name'], subnet_name)
        self._configure_subnet(subnet_network, subnet_mask, domains,
                               subnet_gateway, subnet_primarydns,
                               subnet_secondarydns)
        if orgs:
            self.configure_entity(
                orgs,
                FILTER['subnet_org'],
                tab_locator=tab_locators['tab_org'],
                entity_select=org_select
            )
        self.click(common_locators['submit'])

    def search_and_validate(self, subnet_name):
        """Search Subnet name, network and mask to validate results."""
        result = None
        self.search_and_click(subnet_name)
        if self.wait_until_element(locators['subnet.name']):
            result = dict(
                [('name', None), ('network', None), ('mask', None)])
            result['name'] = self.find_element(
                locators['subnet.name']).get_attribute('value')
            result['network'] = self.find_element(
                locators['subnet.network']).get_attribute('value')
            result['mask'] = self.find_element(
                locators['subnet.mask']).get_attribute('value')
        return result

    def update(self, subnet_name, orgs=None, new_orgs=None, org_select=False,
               new_subnet_name=None, new_subnet_network=None,
               new_subnet_mask=None):
        """Update subnet name, network and mask from UI."""
        self.search_and_click(subnet_name)
        if new_subnet_name:
            self.assign_value(locators['subnet.name'], new_subnet_name)
        self._configure_subnet(new_subnet_network, new_subnet_mask)
        self.configure_entity(
            orgs,
            FILTER['subnet_org'],
            tab_locator=tab_locators['tab_org'],
            new_entity_list=new_orgs,
            entity_select=org_select,
        )
        self.click(common_locators['submit'])
