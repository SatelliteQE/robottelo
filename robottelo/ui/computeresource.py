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
            if parameter_type != 'special select':
                self.assign_value(
                    locators[param_locator], parameter_value)
            else:
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
        self.assign_value(locators['resource.name'], name)
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
        self.click(locators['resource.edit'] % name)
        self.wait_until_element(locators['resource.name'])
        if newname:
            self.assign_value(locators['resource.name'], newname)
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
        self.search_and_click(cr_name)
        self.click(tab_locators['resource.tab_containers'])
        self.assign_value(
            locators['resource.filter_containers'], container_name)
        return self.wait_until_element(
            locators['resource.select_container'] % container_name)

    def list_vms(self, res_name):
        """Lists vms of a particular compute resource.

        Note: Currently lists only vms that show up on the first page.
        """
        self.search_and_click(res_name)
        self.click(tab_locators['resource.tab_virtual_machines'])
        vm_elements = self.find_elements(locators['resource.vm_list'])
        return [vm.text for vm in vm_elements]

    def add_image(self, res_name, parameter_list):
        """Adds an image to a compute resource."""
        self.search_and_click(res_name)
        self.click(locators['resource.image_add'])
        self.wait_until_element(locators['resource.image_name'])
        for parameter_name, parameter_value in parameter_list:
            param_locator = '_'.join((
                'resource.image',
                (parameter_name.lower())
            ))
            self.assign_value(locators[param_locator], parameter_value)
        self.click(locators['resource.image_submit'])

    def list_images(self, res_name):
        """Lists images on Compute Resource.

        Note: Currently lists only images that show up on the first page.
        """
        self.search_and_click(res_name)
        self.click(tab_locators['resource.tab_images'])
        image_elements = self.find_elements(locators['resource.image_list'])
        return [image.text for image in image_elements]

    def vm_action_toggle(self, res_name, vm_name, really):
        """Toggle power status of a vm on the compute resource."""
        self.search_and_click(res_name)
        self.click(tab_locators['resource.tab_virtual_machines'])
        button = self.find_element(
            locators['resource.vm_power_button'] % vm_name
        )
        self.click(button)
        if "Off" in button.text:
            self.handle_alert(really)

    def vm_delete(self, res_name, vm_name, really):
        """Removes a vm from the compute resource."""
        self.search_and_click(res_name)
        self.click(tab_locators['resource.tab_virtual_machines'])
        for locator in [locators['resource.vm_delete_button_dropdown'],
                        locators['resource.vm_delete_button']]:
            self.click(locator % vm_name)
        self.handle_alert(really)

    def search_vm(self, resource_name, vm_name):
        """Searches for existing Virtual machine from particular compute resource. It
        is necessary to use custom search here as we need to select compute
        resource tab before searching for particular Virtual machine and also,
        there is no search button to click
        """
        self.search_and_click(resource_name)
        self.click(tab_locators['resource.tab_virtual_machines'])
        self.assign_value(
            locators['resource.search_filter'], vm_name)
        strategy, value = self._search_locator()
        return self.wait_until_element((strategy, value % vm_name))

    def set_power_status(self, resource_name, vm_name, power_on=None):
        """Perform power on or power off for VM's

        :param bool power_on: True - for On, False - for Off
        """
        status = None
        locator_status = locators['resource.power_status']
        element = self.search_vm(resource_name, vm_name)
        if element is None:
            raise UIError(
                'Could not find Virtual machine "{0}"'.format(vm_name))
        button = self.find_element(
            locators['resource.vm_power_button']
        )
        if power_on is True:
            if 'On' not in button.text:
                raise UIError(
                    'Could not start VM {0}. VM is running'.format(vm_name)
                )
            self.click(button)
            self.search_vm(resource_name, vm_name)
            status = self.wait_until_element(locator_status).text
        elif power_on is False:
            if 'Off' not in button.text:
                raise UIError(
                    'Could not stop VM {0}. VM is not running'.format(vm_name)
                )
            self.click(button, wait_for_ajax=False)
            self.handle_alert(True)
            self.search_vm(resource_name, vm_name)
            status = self.wait_until_element(locator_status).text
        return status
