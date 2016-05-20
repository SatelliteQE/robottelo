"""Utilities to manipulate hosts via UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Hosts(Base):
    """Provides the CRUD functionality for Host."""

    def _configure_hosts_parameters(self, parameters_list):
        """Provide configuration capabilities for host entity generic
        properties.
        All values should be passed in absolute correspondence to UI. For
        example, we need to choose a value from 'Lifecycle environment' select
        list from 'Host' tab and input root password in corresponding field
        from 'Operating System' tab, so next parameter list should be passed::

            [
                ['Host', 'Lifecycle environment', 'Library'],
                ['Operating System', 'Root password', 'mynewpassword123'],
            ]

        """
        for tab_name, parameter_name, parameter_value in parameters_list:
            tab_locator = tab_locators['.tab_'.join((
                'host',
                (tab_name.lower()).replace(' ', '_')
            ))]
            param_locator = locators['.'.join((
                'host',
                (parameter_name.lower()).replace(' ', '_')
            ))]
            self.click(tab_locator)
            if parameter_name == 'Reset Puppet Environment':
                self.click(param_locator)
                continue
            # send_keys() can't send left parenthesis (see
            # SeleniumHQ/selenium#674), which is used in compute resource name
            # (e.g. 'test (Libvirt)')
            elif parameter_name == 'Deploy on' and ' (' in parameter_value:
                self.click(param_locator)
                # typing compute resource name without parenthesis part
                self.text_field_update(
                    common_locators['select_list_search_box'],
                    parameter_value.split(' (')[0]
                )
                strategy, value = common_locators['entity_select_list']
                # selecting compute resource by its full name (with parenthesis
                # part)
                self.click((strategy, value % parameter_value))
                continue
            self.assign_value(param_locator, parameter_value)

    def _configure_interface_parameters(self, parameters_list):
        """Provide configuration capabilities for host entity interface
        All values should be passed in absolute correspondence to UI. For
        example, we need to choose a value from 'Domain' select list and input
        MAC address in corresponding field, so next parameter list should be
        passed::

            [
                ['Domain', host.domain.name],
                ['MAC address', '16:76:20:06:d4:c0'],
            ]

        """
        for parameter_name, parameter_value in parameters_list:
            param_locator = locators['.interface_'.join((
                'host',
                (parameter_name.lower()).replace(' ', '_')
            ))]
            self.assign_value(param_locator, parameter_value)
        self.click(locators['host.save_interface'])

    def _configure_puppet_modules(self, puppet_modules_list):
        """Provide configuration capabilities for host entity puppet classes
        tab.
        """
        self.click(tab_locators['host.tab_puppet_classes'])
        strategy1, value1 = locators['host.select_puppetmodule']
        strategy2, value2 = locators['host.select_puppetclass']
        for puppet_module in puppet_modules_list:
            self.click((strategy1, value1 % puppet_module))
            self.click((strategy2, value2 % puppet_module))

    def _add_host_parameters(self, parameters_list):
        """Add new host parameters for 'parameters' tab. Example::

        host_parameters=[['test01', 'value01'], ['test02', 'value02'],
        ['test03', 'value03']]

        """
        self.click(tab_locators['host.tab_params'])
        strategy1, value1 = locators['host.host_parameter_name']
        strategy2, value2 = locators['host.host_parameter_value']
        index = 1
        for parameter_name, parameter_value in parameters_list:
            self.click(locators['host.add_new_host_parameter'])
            self.text_field_update((strategy1, value1 % index), parameter_name)
            self.text_field_update(
                (strategy2, value2 % index), parameter_value)
            index += 1

    def create(self, name, parameters_list=None, puppet_classes=None,
               interface_parameters=None, host_parameters=None, ):
        """Creates a host."""
        self.click(locators['host.new'])
        self.text_field_update(locators['host.name'], name)
        if parameters_list is not None:
            self._configure_hosts_parameters(parameters_list)
        if puppet_classes is not None:
            self._configure_puppet_modules(puppet_classes)
        if interface_parameters:
            self.click(tab_locators['host.tab_interfaces'])
            self.click(locators['host.edit_default_interface'])
            self._configure_interface_parameters(interface_parameters)
        if host_parameters:
            self._add_host_parameters(host_parameters)
        self.wait_until_element_is_not_visible(
            common_locators['modal_background'])
        self.click(common_locators['submit'])

    def update(self, name, domain_name, new_name=None, parameters_list=None,
               puppet_classes=None, interface_parameters=None,
               host_parameters=None):
        """Updates a Host."""
        element = self.search(u'{0}.{1}'.format(name, domain_name))
        self.click(element)
        self.click(locators['host.edit'])
        if new_name:
            self.wait_until_element(locators['host.name'])
            self.field_update('host.name', new_name)
        if parameters_list is not None:
            self._configure_hosts_parameters(parameters_list)
        if puppet_classes is not None:
            self._configure_puppet_modules(puppet_classes)
        if interface_parameters:
            self.click(tab_locators['host.tab_interfaces'])
            self.click(locators['host.edit_default_interface'])
            self._configure_interface_parameters(interface_parameters)
        if host_parameters:
            self._add_host_parameters(host_parameters)
        self.wait_until_element_is_not_visible(
            common_locators['modal_background'])
        self.click(common_locators['submit'])

    def navigate_to_entity(self):
        """Navigate to Hosts entity page"""
        Navigator(self.browser).go_to_hosts()

    def _search_locator(self):
        """Specify locator for Hosts entity search procedure"""
        return locators['host.select_name']

    def delete(self, name, really=True):
        """Deletes a host."""
        self.delete_entity(
            name,
            really,
            locators['host.delete'],
            drop_locator=locators['host.dropdown'],
        )

    def update_host_bulkactions(self, host=None, org=None):
        """Updates host via bulkactions"""
        strategy1, value1 = locators['host.checkbox']
        self.click((strategy1, value1 % host))
        self.click(locators['host.select_action'])
        if org:
            self.click(locators['host.assign_org'])
            self.click(locators['host.fix_mismatch'])
            self.select(locators['host.select_org'], org)
        self.click(locators['host.bulk_submit'])
