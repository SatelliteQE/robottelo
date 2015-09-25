# -*- encoding: utf-8 -*-
"""Implements Subnet UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators


class Subnet(Base):
    """Provides the CRUD functionality for Subnet."""
    def _configure_subnet(self, subnet_network, subnet_mask, domains=None,
                          subnet_gateway=None, subnet_primarydns=None,
                          subnet_secondarydns=None):
        """Configures the subnet."""
        domain_tablocator = tab_locators['subnet.tab_domain']
        if subnet_network:
            if self.wait_until_element(locators['subnet.network']):
                self.text_field_update(locators['subnet.network'],
                                       subnet_network)
        if subnet_mask:
            if self.wait_until_element(locators['subnet.mask']):
                self.text_field_update(locators['subnet.mask'],
                                       subnet_mask)
        if subnet_gateway:
            if self.wait_until_element(locators['subnet.gateway']):
                self.text_field_update(locators['subnet.gateway'],
                                       subnet_gateway)
        if subnet_primarydns:
            if self.wait_until_element(locators['subnet.primarydns']):
                self.text_field_update(locators['subnet.primarydns'],
                                       subnet_primarydns)
        if subnet_secondarydns:
            if self.wait_until_element(locators['subnet.secondarydns']):
                self.text_field_update(locators['subnet.secondarydns'],
                                       subnet_secondarydns)
        if domains:
            self.configure_entity(domains, FILTER['sub_domain'],
                                  tab_locator=domain_tablocator)

    def create(self, orgs, subnet_name=None,
               subnet_network=None, subnet_mask=None, subnet_gateway=None,
               subnet_primarydns=None, subnet_secondarydns=None,
               domains=None, org_select=True):
        """Create Subnet from UI"""
        self.click(locators['subnet.new'])

        if self.wait_until_element(locators['subnet.name']):
            self.find_element(locators['subnet.name']).send_keys(subnet_name)
        self._configure_subnet(subnet_network, subnet_mask, domains,
                               subnet_gateway, subnet_primarydns,
                               subnet_secondarydns)
        if orgs:
            self.configure_entity(orgs, FILTER['subnet_org'],
                                  tab_locator=tab_locators['tab_org'],
                                  entity_select=org_select)
        self.click(common_locators['submit'])

    def delete(self, subnet_name, really=True):
        """Remove subnet from UI."""
        self.delete_entity(
            subnet_name,
            really,
            locators['subnet.display_name'],
            locators['subnet.delete'],
        )

    def search_subnet(self, subnet_name):
        """Search Subnet name, network and mask to validate results."""
        result = None
        if len(subnet_name) <= 30:
            subnet_object = self.search_entity(
                subnet_name, locators['subnet.display_name'])
        else:
            subnet_object = self.search_entity(
                subnet_name, common_locators['select_filtered_entity'])
        if subnet_object:
            subnet_object.click()
            if self.wait_until_element(locators['subnet.name']):
                result = dict([('name', None), ('network', None),
                               ('mask', None)])
                result['name'] = self.find_element(
                    locators['subnet.name']
                ).get_attribute('value')
                result['network'] = self.find_element(
                    locators['subnet.network']
                ).get_attribute('value')
                result['mask'] = self.find_element(
                    locators['subnet.mask']
                ).get_attribute('value')
        return result

    def update(self, subnet_name, orgs=None, new_orgs=None, org_select=False,
               new_subnet_name=None, new_subnet_network=None,
               new_subnet_mask=None):
        """Update subnet name, network and mask from UI."""
        subnet_object = self.search_entity(
            subnet_name, locators['subnet.display_name'])

        if subnet_object:
            subnet_object.click()
            if new_subnet_name:
                if self.wait_until_element(locators['subnet.name']):
                    self.field_update('subnet.name', new_subnet_name)
            self._configure_subnet(new_subnet_network, new_subnet_mask)
            self.configure_entity(
                orgs,
                FILTER['subnet_org'],
                tab_locator=tab_locators['tab_org'],
                new_entity_list=new_orgs,
                entity_select=org_select,
            )
            self.click(common_locators['submit'])
