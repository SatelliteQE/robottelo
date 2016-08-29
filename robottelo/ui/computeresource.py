# -*- encoding: utf-8 -*-
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UINoSuchElementError, UIError
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
                self.assign_value(locators[param_locator], parameter_value)

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
        """Updates compute resource entity."""
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
        """Removes the compute resource entity."""
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

    def list_vms(self, res_name):
        """Lists vms of a particular compute resource.

        Note: Currently lists only vms that show up on the first page.
        """
        self.click(self.search(res_name))
        self.click(tab_locators['resource.tab_virtual_machines'])
        vm_elements = self.find_elements(locators['resource.vm_list'])
        return [vm.text for vm in vm_elements]

    def add_image(self, res_name, parameter_list):
        """Adds an image to a compute resource."""
        self.click(self.search(res_name))
        self.click(locators['resource.image_add'])
        self.wait_until_element(locators['resource.image_name'])
        for parameter_name, parameter_value, parameter_type in parameter_list:
            param_locator = '.'.join((
                'resource.image',
                (parameter_name.lower()).replace(' ', '_')
            ))
        self.assign_value(locators[param_locator], parameter_value)
        self.click(locators['resource.image_submit'])

    def list_images(self, res_name):
        """Lists images on Compute Resource.

        Note: Currently lists only images that show up on the first page.
        """
        self.click(self.search(res_name))
        self.click(tab_locators['tab_images'])
        image_elements = self.find_elements(locators['resource.image_list'])
        return [image.text for image in image_elements]

    def vm_action_stop(self, res_name, vm_name, really):
        """Stops a vm on the compute resource."""
        self.click(self.search(res_name))
        self.click(tab_locators['resource.tab_virtual_machines'])
        button = self.find_element(
            locators['resource.vm_power_button'] % vm_name
        )
        if 'Off' not in button.text:
            raise UIError(
                'Could not stop VM {0}. VM is not running'.format(vm_name)
            )
        self.click(button)
        self.handle_alert(really)

    def vm_action_start(self, res_name, vm_name):
        """Starts a vm on the compute resource."""
        self.click(self.search(res_name))
        self.click(tab_locators['resource.tab_virtual_machines'])
        button = self.find_element(
            locators['resource.vm_power_button'] % vm_name
        )
        if 'On' not in button.text:
            raise UIError(
                'Could not start VM {0}. VM is already running'.format(vm_name)
            )
        self.click(button)

    def vm_action_toggle(self, res_name, vm_name, really):
        """Toggle power status of a vm on the compute resource."""
        self.click(self.search(res_name))
        self.click(tab_locators['resource.tab_virtual_machines'])
        button = self.find_element(
            locators['resource.vm_power_button'] % vm_name
        )
        self.click(button)
        if "Off" in button.text:
            self.handle_alert(really)

    def vm_delete(self, res_name, vm_name, really):
        """Removes a vm from the compute resource."""
        self.click(self.search(res_name))
        self.click(tab_locators['resource.tab_virtual_machines'])
        for locator in [locators['resource.vm_delete_button_dropdown'],
                        locators['resource.vm_delete_button']]:
            self.click(locator % vm_name)
        self.handle_alert(really)
