# -*- encoding: utf-8 -*-
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UINoSuchElementError, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


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
            Select(
                self.find_element(locators['resource.provider_type'])
            ).select_by_visible_text(provider_type)
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
                Select(
                    self.find_element(locators[param_locator])
                ).select_by_visible_text(parameter_value)
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
                Select(
                    self.find_element(locators[param_locator])
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
        self.click(common_locators['submit'], wait_for_ajax=False)

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
        Navigator(self.browser).go_to_compute_resources()
        self.delete_entity(
            name,
            really,
            locators['resource.delete'],
            drop_locator=locators['resource.dropdown'],
        )

    def go_to_compute_resource(self, res_name):
        """ Navigates to compute resource page """
        resource = self.search(res_name)
        if resource is None:
            raise UINoSuchElementError(
                'Could not find the resource {0}'.format(res_name))
        strategy, value = locators['resource.get_by_name']
        locator = (strategy, value % res_name)
        self.click(locator, wait_for_ajax=False)
        self.wait_until_element(locators['resource.virtual_machines_tab'])

    def list_vms(self, res_name):
        """ Lists vms on compute resource
        note: lists only vms that show up on the first page
        """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.virtual_machines_tab'])
        vms = self.browser.find_elements_by_xpath(
            "//table[contains(@id, 'DataTables')]//a[contains(@data-id, '%s')]"
            % res_name)
        return vms

    def add_image(self, res_name, parameter_list):
        """ Adds an image to a compute resource """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.image.add'])
        self.wait_until_element(locators['resource.image.name'])
        if parameter_list is None:
            return
        for parameter_name, parameter_value, parameter_type in parameter_list:
            param_locator = '.'.join((
                'resource.image',
                (parameter_name.lower()).replace(' ', '_')
            ))
            if parameter_type == 'field':
                self.find_element(
                    locators[param_locator]).send_keys(parameter_value)
            elif parameter_type == 'select':
                Select(
                    self.find_element(locators[param_locator])
                ).select_by_visible_text(parameter_value)
        self.click(locators['resource.image.submit'])
        self.wait_until_element(common_locators['notif.success'])

    def list_images(self, res_name):
        """ Lists images on compute resource
        note: lists only images that show up on the first page
        """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.images_tab'])
        images = self.browser.find_elements_by_xpath(
            "//table[contains(@id, 'DataTables_Table_0')]/tbody/tr/*[1]")
        return images

    def vm_action_stop(self, res_name, vm_name, really):
        """ Stops a vm on the compute resource """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.virtual_machines_tab'])
        strategy, value = locators['resource.vm.power_button']
        locator = (strategy, value % (res_name, vm_name))
        button = self.find_element(locator)
        if 'Off' in button.text:
            self.click(locator, wait_for_ajax=False)
            self.handle_alert(really)
            # note: this should probably have a timeout
            self.wait_until_element(common_locators['notif.success'])
        else:
            raise UIError(
                'Could not stop VM {0}. VM is not running'.format(vm_name)
            )

    def vm_action_start(self, res_name, vm_name):
        """ Starts a vm on the compute resource """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.virtual_machines_tab'])
        strategy, value = locators['resource.vm.power_button']
        locator = (strategy, value % (res_name, vm_name))
        button = self.find_element(locator)
        if 'On' in button.text:
            self.click(locator, wait_for_ajax=False)
            # note: this should probably have a timeout
            self.wait_until_element(common_locators['notif.success'])
        else:
            raise UIError(
                'Could not start VM {0}. VM is already running'.format(vm_name)
            )

    def vm_action_toggle(self, res_name, vm_name, really):
        """ Toggle power status of a vm on the compute resource """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.virtual_machines_tab'])
        strategy, value = locators['resource.vm.power_button']
        locator = (strategy, value % (res_name, vm_name))
        button = self.find_element(locator)
        if "On" in button.text:
            self.click(locator, wait_for_ajax=False)
            self.wait_until_element(common_locators['notif.success'])
        else:
            self.click(locator, wait_for_ajax=False)
            self.handle_alert(really)
            self.wait_until_element(common_locators['notif.success'])

    def vm_delete(self, res_name, vm_name, really):
        """ Removes a vm from the compute resource """
        self.go_to_compute_resource(res_name)
        self.click(locators['resource.virtual_machines_tab'])
        strategy, value = locators['resource.vm.delete_button_dropdown']
        locator = (strategy, value % (res_name, vm_name))
        self.click(locator)
        strategy, value = locators['resource.vm.delete_button']
        locator = (strategy, value % (res_name, vm_name))
        self.click(locator, wait_for_ajax=False)
        self.handle_alert(really)
        self.wait_until_element(common_locators['notif.success'])
