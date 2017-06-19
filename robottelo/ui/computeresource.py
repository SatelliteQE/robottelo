# -*- encoding: utf-8 -*-
from robottelo.constants import FILTER, FOREMAN_PROVIDERS
from robottelo.ui.base import Base, UINoSuchElementError, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class ResourceProfileFormBase(object):
    """Base class for compute resources profiles forms"""
    _page = None
    # some fields are like two panel and to select from the left one to the
    # right as users groups and roles
    # please see how implemented in ResourceProfileFormEC2 for security_groups
    selector_fields = []
    # some fields can be part of sections that can be added
    # like storage and networks, please how implemented in
    # ResourceProfileFormRHEV (implement network_interfaces and storage)
    group_fields_locators = {}

    def __init__(self, page):
        """Initiate compute resource profile form

        :type page: ComputeProfile
        :param page: The compute profile object ComputeProfile or
            ComputeResource
        """
        self._page = page

    @property
    def page(self):
        """Return the current page ComputeResource or ComputeProfile"""
        return self._page

    def _clean_value(self, name, value):
        """Check some values and correct them accordingly"""
        if name in self.selector_fields:
            if not isinstance(value, (list, tuple)):
                value = [value]
        return value

    def set_value(self, name, value):
        """Set the value of the corresponding field in UI"""
        locator_attr = '{0}_locator'.format(name)
        locator = getattr(self, locator_attr, None)
        if locator is None and name not in self.group_fields_locators:
            raise UIError('Field name: {0} not supported'.format(name))
        value = self._clean_value(name, value)
        if name in self.selector_fields:
            self.page.configure_entity(value, locator)
        elif name in self.group_fields_locators:
            field_index = 0
            group_fields_locators = self.group_fields_locators[name]
            add_node_locator = group_fields_locators['_add_node']
            for group_field in value:
                if group_field is not None:
                    for field_key, field_value in group_field.items():
                        field_locator = group_fields_locators.get(field_key)
                        available_fields = self.page.find_elements(
                            field_locator)
                        if len(available_fields)-1 < field_index:
                            self.page.click(add_node_locator)
                            available_fields = self.page.find_elements(
                                field_locator)
                        self.page.assign_value(
                            available_fields[field_index], field_value)

                field_index += 1
        else:
            self.page.assign_value(locator, value)

    def set_values(self, **kwargs):
        """Set the values of the corresponding fields in UI"""
        for key, value in kwargs.items():
            self.set_value(key, value)

    def submit(self):
        """Press the submit form button"""
        self.page.click(common_locators['submit'])


class ResourceProfileFormEC2(ResourceProfileFormBase):
    """Implement EC2 compute resource profile form"""

    flavor_locator = locators["resource.compute_profile.ec2_flavor"]
    image_locator = locators["resource.compute_profile.ec2_image"]
    subnet_locator = locators["resource.compute_profile.ec2_subnet"]
    managed_ip_locator = locators["resource.compute_profile.ec2_managed_ip"]
    availability_zone_locator = locators[
        "resource.compute_profile.ec2_availability_zone"]
    security_groups_locator = FILTER['ec2_security_groups']
    selector_fields = ['security_groups']

    def _clean_value(self, name, value):
        """Check some values and correct them accordingly"""
        value = ResourceProfileFormBase._clean_value(self, name, value)
        if not value:
            if name == 'availability_zone':
                value = 'No preference'
            elif name == 'subnet':
                value = 'EC2'
            elif name == 'security_groups':
                value = []
        return value


class ResourceProfileFormRHEV(ResourceProfileFormBase):
    """Implement RHEV compute resource profile form"""

    cluster_locator = locators["resource.compute_profile.rhev_cluster"]
    template_locator = locators["resource.compute_profile.rhev_template"]
    cores_locator = locators["resource.compute_profile.rhev_cores"]
    memory_locator = locators["resource.compute_profile.rhev_memory"]
    image_locator = locators["resource.compute_profile.rhev_image"]
    group_fields_locators = dict(
        network_interfaces=dict(
            _add_node=locators[
                "resource.compute_profile.rhev_interface_add_node"],
            name=locators["resource.compute_profile.rhev_interface_name"],
            network=locators["resource.compute_profile.rhev_interface_network"]
        ),
        storage=dict(
            _add_node=locators[
                "resource.compute_profile.rhev_storage_add_node"],
            size=locators["resource.compute_profile.rhev_storage_size"],
            storage_domain=locators[
                "resource.compute_profile.rhev_storage_domain"],
            preallocate_disk=locators[
                "resource.compute_profile.rhev_storage_preallocate"],
            bootable=locators["resource.compute_profile.rhev_storage_bootable"]
        )
    )

    def set_values(self, **kwargs):
        """Set the values of the corresponding fields in UI"""
        # if template is the fields to set, it set in priority as, when
        # selecting a template, configuration data is loaded in UI
        template_key = 'template'
        template = kwargs.get(template_key)
        if template is not None:
            self.set_value(template_key, template)
            del kwargs[template_key]
        ResourceProfileFormBase.set_values(self, **kwargs)


_compute_resource_profiles = {
    FOREMAN_PROVIDERS['ec2']: ResourceProfileFormEC2,
    FOREMAN_PROVIDERS['rhev']: ResourceProfileFormRHEV,
}


def get_compute_resource_profile(page, res_type=None):
    """Return the corresponding instance compute resource profile form object
    """
    resource_profile_class = _compute_resource_profiles.get(res_type)
    if not resource_profile_class:
        raise UIError(
            'Resource profile for resource type: {0}'
            ' not supported'.format(res_type)
        )

    return resource_profile_class(page)


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

    def select_profile(self, resource_name, profile_name):
        """Select the compute profile of a specific compute resource

        :param resource_name: Name of compute resource to select from the list
        :param profile_name: Name of profile that contains required compute
            resource (e.g. '2-Medium' or '1-Small')
        :return: resource type and the resource profile form element
        :returns: tuple
        """
        resource_element = self.search(resource_name)
        resource_type = self.wait_until_element(
            locators['resource.resource_type'] % resource_name).text
        self.click(resource_element)
        self.click(tab_locators['resource.tab_compute_profiles'])
        self.click(locators["resource.compute_profile"] % profile_name)
        return (resource_type,
                self.wait_until_element(locators['profile.resource_form']))

    def set_profile_values(self, resource_name, profile_name, **kwargs):
        """Fill and Submit the compute resource profile form configuration
        properties

        :param resource_name: Name of compute resource to select from the list
        :param profile_name: Name of profile that contains required compute
            resource (e.g. '2-Medium' or '1-Small')
        :param kwargs: the compute resource profile configuration properties
            fields to be set
        """
        resource_type, _ = self.select_profile(resource_name, profile_name)
        resource_profile_form = get_compute_resource_profile(
            self, resource_type)
        resource_profile_form.set_values(**kwargs)
        resource_profile_form.submit()
