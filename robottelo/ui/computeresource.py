# -*- encoding: utf-8 -*-
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class ComputeResource(Base):
    """Provides the CRUD functionality for Compute Resources."""

    def navigate_to_entity(self):
        """Navigate to Compute Resource entity page"""
        Navigator(self.browser).go_to_compute_resources()

    def _search_locator(self):
        """Specify locator for Compute Resource entity search procedure"""
        return locators['resource.select_name']

    def _configure_resource_provider(
            self, provider_type=None, parameter_list=None):
        """Provide configuration capabilities for compute resource provider.
        All values should be passed in absolute correspondence to UI. For
        example, we need to input some data to 'URL' field, select checkbox
        'Console Passwords' and choose 'SPICE' value from select list, so next
        parameter list should be passed::

            [
                ['URL', libvirt_url, 'field'],
                ['Display Type', 'SPICE', 'select'],
                ['Console passwords', False, 'checkbox']
            ]

        We have cases when it is necessary to push a button to populate values
        for select list. For such scenarios we have 'special select' parameter
        type. For example, for 'RHEV' provider, we need to click 'Load
        Datacenters' button to get values for 'Datacenter' list::

            [
                ['Description', 'My_Test', 'field'],
                ['URL', libvirt_url, 'field'],
                ['Username', 'admin', 'field'],
                ['Password', 'test', 'field'],
                ['X509 Certification Authorities', 'test', 'field'],
                ['Datacenter', 'test', 'special select'],
            ]

        """
        if provider_type:
            self.select(locators['resource.provider_type'], provider_type)
        if parameter_list is None:
            return
        for parameter_name, parameter_value, parameter_type in parameter_list:
            param_locator = '.'.join((
                'resource',
                (parameter_name.lower()).replace(' ', '_')
            ))
            self.wait_until_element(locators[param_locator])
            if parameter_type == 'field':
                self.text_field_update(
                    locators[param_locator], parameter_value)
            elif parameter_type == 'select':
                self.select(locators[param_locator], parameter_value)
            elif parameter_type == 'checkbox':
                if (self.find_element(locators[param_locator]).is_selected() !=
                        parameter_value):
                    self.click(locators[param_locator])
            elif parameter_type == 'special select':
                button_locator = '.'.join((
                    'resource',
                    (parameter_name.lower()).replace(' ', '_'),
                    'button'
                ))
                self.click(locators[button_locator])
                self.find_element(
                    locators[param_locator]
                ).select_by_visible_text(parameter_value)

    def _configure_orgs(self, orgs, org_select):
        """Provides configuration capabilities for compute resource
        organization. The following format should be used::

            orgs=['Aoes6V', 'JIFNPC'], org_select=True

        """
        self.configure_entity(
            orgs,
            FILTER['cr_org'],
            tab_locator=tab_locators['tab_org'],
            entity_select=org_select
        )

    def _configure_locations(self, locations, loc_select):
        """Provides configuration capabilities for compute resource location

        The following format should be used::

            locations=['Default Location'], loc_select=True

        """
        self.configure_entity(
            locations,
            FILTER['cr_loc'],
            tab_locator=tab_locators['tab_loc'],
            entity_select=loc_select
        )

    def create(self, name, provider_type, parameter_list,
               orgs=None, org_select=None, locations=None, loc_select=None):
        """Creates a compute resource."""
        self.click(locators['resource.new'])
        if self.wait_until_element(locators['resource.name']):
            self.find_element(locators['resource.name']).send_keys(name)
        self._configure_resource_provider(provider_type, parameter_list)
        if locations:
            self._configure_locations(locations, loc_select)
        if orgs:
            self._configure_orgs(orgs, org_select)
        self.click(common_locators['submit'])

    def update(self, name, newname=None, parameter_list=None,
               orgs=None, org_select=None, locations=None, loc_select=None):
        """Updates compute resource entity"""
        element = self.search(name)
        if element is None:
            raise UINoSuchElementError(
                'Could not find the resource {0}'.format(name))
        strategy, value = locators['resource.edit']
        self.click((strategy, value % name))
        self.wait_until_element(locators['resource.name'])
        if newname:
            self.field_update('resource.name', newname)
        self._configure_resource_provider(parameter_list=parameter_list)
        if locations:
            self._configure_locations(locations, loc_select)
        if orgs:
            self._configure_orgs(orgs, org_select)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Removes the compute resource entity"""
        self.delete_entity(
            name,
            really,
            locators['resource.delete'],
            drop_locator=locators['resource.dropdown'],
        )

    def search_container(self, cr_name, container_name):
        """Searches for specific container located in compute resource under
        'Containers' tab
        """
        self.click(self.search(cr_name))
        self.click(tab_locators['resource.tab_containers'])
        self.text_field_update(
            locators['resource.filter_containers'], container_name)
        strategy, value = locators['resource.select_container']
        return self.wait_until_element((strategy, value % container_name))
