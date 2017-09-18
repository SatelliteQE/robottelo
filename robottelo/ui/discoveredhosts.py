# -*- encoding: utf-8 -*-
"""Implements Discovered Hosts from UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from time import sleep


class DiscoveredHosts(Base):
    """Manipulates Discovered Hosts from UI"""

    def navigate_to_entity(self):
        """Navigate to Discovered Hosts entity page"""
        Navigator(self.browser).go_to_discovered_hosts()

    def _search_locator(self):
        """Specify locator for Discovered Hosts entity search procedure"""
        return locators["discoveredhosts.hostname"]

    def delete_from_facts(self, hostname, really=True):
        """Delete existing discovered host from facts page"""
        host = self.search(hostname)
        if not host:
            raise UIError(
                'Could not find the selected discovered host "{0}"'
                .format(hostname)
            )
        self.click(host)
        strategy, value = locators['discoveredhosts.delete_from_facts']
        self.click((strategy, value % hostname), wait_for_ajax=False)
        self.handle_alert(really)

    def multi_delete(self, hostnames, really=True):
        """Bulk delete discovered hosts"""
        select_host = locators['discoveredhosts.select_host']
        select_action_element = locators['discoveredhosts.select_action']
        multi_delete_element = locators['discoveredhosts.multi_delete']
        bulk_submit_button = locators['discoveredhosts.bulk_submit_button']
        for host in hostnames:
            self.click((select_host % host))
        if not self.find_element(select_action_element):
            raise UIError(
                'Could not find the select_action dropdown for bulk operations'
            )
        self.click(select_action_element)
        if not self.find_element(multi_delete_element):
            raise UIError(
                'Could not find the delete option from select_action dropdown'
            )
        self.click(multi_delete_element)
        if not self.find_element(bulk_submit_button):
            raise UIError(
                'Could not find the bulk submit button'
            )
        self.click(bulk_submit_button)

    def refresh_facts(self, hostname):
        """Refresh the facts of discovered host"""
        host = self.search(hostname)
        if not host:
            raise UIError(
                'Could not find the selected discovered host "{0}"'
                .format(hostname)
            )
        self.click(locators['discoveredhosts.dropdown'] % hostname)
        self.click(locators['discoveredhosts.refresh_facts'] % hostname)

    def waitfordiscoveredhost(self, hostname):
        """Check if host is visible under 'Discovered Hosts' on UI

        Introduced a delay of 300secs by polling every 10 secs to see if
        unknown host gets discovered and become visible on UI
        """
        for _ in range(30):
            discovered_host = self.search(hostname)
            if discovered_host:
                return True
            else:
                sleep(10)
        return False

    def fetch_fact_value(self, hostname, element):
        """Fetch the value of selected fact from discovered hosts page"""
        host = self.search(hostname)
        if not host:
            raise UIError(
                'Could not find the selected discovered host "{0}"'
                .format(hostname)
            )
        web_element = self.find_element(element)
        if not web_element:
            raise UIError(
                'Could not find element from discovered host page'
            )
        element_value = web_element.text
        return element_value

    def reboot_host(self, hostname):
        """Reboot the discovered host"""
        host = self.search(hostname)
        if not host:
            raise UIError(
                'Could not find the selected discovered host "{0}"'
                .format(hostname)
            )
        self.click(locators['discoveredhosts.dropdown'] % hostname)
        self.click(
            locators['discoveredhosts.reboot'] % hostname,
            wait_for_ajax=False
        )

    def auto_provision(self, hostname):
        """Auto provision the discovered host from dropdown"""
        host = self.search(hostname)
        if not host:
            raise UIError(
                'Could not find the selected discovered host "{0}"'
                .format(hostname)
            )
        # Manually provision the host by selecting 'auto_provision' option
        self.click(locators['discoveredhosts.dropdown'] % hostname)
        self.click(locators['discoveredhosts.auto_provision'] % hostname)

    def auto_provision_all(self):
        """Auto provision all the discovered hosts"""
        self.navigate_to_entity()
        self.click(locators["discoveredhosts.auto_provision_all"])

    def update_org_loc(self, hostnames, new_org=None, new_loc=None):
        """Update the default org or location for bulk of discovered hosts"""
        self.navigate_to_entity()
        for host in hostnames:
            self.click(locators['discoveredhosts.select_host'] % host)
        self.click(locators['discoveredhosts.select_action'])
        if new_org:
            self.click(locators['discoveredhosts.assign_org'])
            self.select(locators['discoveredhosts.select_org'], new_org)
        if new_loc:
            self.click(locators['discoveredhosts.assign_loc'])
            self.select(locators['discoveredhosts.select_loc'], new_loc)
        self.click(locators['discoveredhosts.bulk_submit_button'])

    def provision_discoveredhost(self, hostgroup, org, loc, hostname,
                                 new_name=None, parameters_list=None,
                                 puppet_classes=None,
                                 interface_parameters=None,
                                 host_parameters=None, quick_create=False,
                                 facts_page=False):
        """Creates a host."""
        if facts_page:
            self.search_and_click(hostname)
            self.click(locators['discoveredhosts.select_action_facts'])
            self.click(locators['discoveredhosts.provision_from_facts'])
        else:
            self.click(locators['discoveredhosts.provision'] % hostname)
        self.select(
            locators['discoveredhosts.select_modal_hostgroup'],
            hostgroup
        )
        self.select(locators['discoveredhosts.select_modal_org'], org)
        self.select(locators['discoveredhosts.select_modal_loc'], loc)
        if not quick_create:
            self.click(locators['discoveredhosts.create_host_button'])
            if new_name is not None:
                self.assign_value(locators['host.name'], new_name)
            if parameters_list is not None:
                self.hosts._configure_hosts_parameters(parameters_list)
            self.wait_until_element_is_not_visible(
                common_locators['modal_background'])
            self.click(common_locators['submit'])
        else:
            self.click(locators['discoveredhosts.quick_create_button'])
