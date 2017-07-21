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
        self.search_and_click(u'{0}.{1}'.format(name, domain_name))
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

    def add_interface(self, name, domain_name, interface_parameters):
        """Adds an interface to host.

        :param name: host's name (without domain part)
        :param domain_name: host's domain name
        :param interface_parameters: A list of interface parameters. Each
            parameter should be a separate list containing tab name and
            parameter name in absolute correspondence to UI (Similar to
            interface parameters list passed to create a host). Example::

                [
                    ['Domain', host.domain.name],
                    ['MAC address', '16:76:20:06:d4:c0'],
                ]
        """
        self.search_and_click(u'{0}.{1}'.format(name, domain_name))
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_interfaces'])
        self.click(locators['host.add_interface'])
        self._configure_interface_parameters(interface_parameters)
        self.click(common_locators['submit'])

    def delete_interface(self, name, domain_name, interface_id=None,
                         interface_mac=None):
        """Deletes interface from host.

        As there's no required unique parameter for interface identification,
        either interface identifier or MAC address should be specified to
        locate the interface.

        Note that there's no confirmation dialog and in case interface can't be
        deleted no exception will be risen.

        :param name: host's name (without domain part)
        :param domain_name: host's domain name
        :param str optional interface_id: interface identifier
        :param str optional interface_mac: interface MAC address
        """
        identifier = interface_id or interface_mac
        if identifier is None:
            raise TypeError(
                'Either `interface_id` or `interface_mac` argument is required'
                ' to locate the interface'
            )
        self.search_and_click(u'{0}.{1}'.format(name, domain_name))
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_interfaces'])
        strategy, value = locators['host.delete_interface']
        self.click((strategy, value % identifier))
        self.click(common_locators['submit'])

    def update_host_bulkactions(
            self, hosts=None, action=None, parameters_list=None):
        """Updates host via bulkactions

        :param hosts: List of hosts that should be selected for action
        :param action: Specify exact action to perform according to UI list. At
            that moment we support only Assign Organization and Run Job actions
        :param parameters_list: List of parameters that are needed for the
            dialogs that go after necessary action was selected. For example::

            [{'organization': 'My_org01'}]
            [{'command': 'ls'}]
        """
        self.navigate_to_entity()
        for host in hosts:
            strategy, value = locators['host.checkbox']
            self.click((strategy, value % host))
        self.click(locators['host.select_action_list'])
        strategy, value = locators['host.select_action']
        self.click((strategy, value % action))
        if parameters_list:
            for parameter in parameters_list:
                if action == 'Assign Organization':
                    self.click(locators['host.fix_mismatch'])
                    self.assign_value(
                        locators['host.select_org'],
                        parameter['organization']
                    )
                    self.click(locators['host.bulk_submit'])
                if action == 'Run Job':
                    self.assign_value(
                        locators['job_invocation.command'],
                        parameter['command']
                    )
                    self.click(common_locators['submit'])
                if action == 'Delete Hosts':
                    self.click(locators['host.bulk_submit'])
                    return self.wait_until_element(
                        locators['task.finished_state'],
                        timeout=parameter['timeout'],
                    )

    def fetch_host_parameters(self, name, domain_name, parameters_list):
        """Fetches parameter values of specified host

        :param name: host's name (without domain part)
        :param domain_name: host's domain name
        :param parameters_list: A list of parameters to be fetched. Each
            parameter should be a separate list containing tab name and
            parameter name in absolute correspondence to UI (Similar to
            parameters list passed to create a host). Example::

                [
                    ['Host', 'Lifecycle Environment'],
                    ['Host', 'Content View'],
                ]

        :return: Dictionary of parameter name - parameter value pairs
        :rtype: dict
        """
        host = self.search(u'{0}.{1}'.format(name, domain_name))
        self.click(host)
        self.click(locators['host.edit'])
        result = {}
        for tab_name, param_name in parameters_list:
            tab_locator = tab_locators['.tab_'.join((
                'host',
                (tab_name.lower()).replace(' ', '_')
            ))]
            param_locator = locators['.fetch_'.join((
                'host',
                (param_name.lower()).replace(' ', '_')
            ))]
            self.click(tab_locator)
            result[param_name] = self.wait_until_element(param_locator).text
        return result

    def get_yaml_output(self, name):
        """Return YAML output for specific host

        :param str name: Name of Host to read information from
        """
        self.click(self.search(name))
        self.click(locators['host.yaml_button'])
        output = self.wait_until_element(locators['host.yaml_output']).text
        self.browser.back()
        self.wait_for_ajax()
        return output

    def get_smart_variable_value(self, host_name, sv_name, hidden=False):
        """Return smart variable value element for specific host

        :param str host_name: Name of Host to get smart variable information
            from
        :param str sv_name: Name of Smart Variable to be read
        :param bool hidden: Specify whether it is expected that read value is
            hidden on UI or not
        """
        self.click(self.search(host_name))
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_params'])
        if hidden:
            strategy, value = locators['host.smart_variable_value_hidden']
        else:
            strategy, value = locators['host.smart_variable_value']
        return self.wait_until_element((strategy, value % sv_name))

    def set_smart_variable_value(self, host_name, sv_name, sv_value,
                                 override=True, hidden=False):
        """Set smart variable value for specific host

        :param str host_name: Name of Host where smart variable value should be
            modified
        :param str sv_name: Name of Smart Variable to be modified
        :param str sv_value: Value of Smart Variable that should be set
        :param bool override: Specify whether it is expected to override smart
            value or just edit its value
        :param bool hidden: Specify whether it is expected that smart variable
            value is hidden on UI or not
        """
        self.click(self.search(host_name))
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_params'])
        if override:
            strategy, value = locators['host.smart_variable_override']
            self.click((strategy, value % sv_name))
        if hidden:
            strategy, value = locators['host.smart_variable_value_hidden']
        else:
            strategy, value = locators['host.smart_variable_value']
        self.assign_value((strategy, value % sv_name), sv_value)
        self.click(common_locators['submit'])

    def get_host_properties(self, host, parameters_list):
        """Get necessary host properties by theirs names"""
        self.search_and_click(host)
        result = {}
        for parameter_name in parameters_list:
            locator = locators['.property_'.join(
                ('host', (parameter_name.lower()).replace(' ', '_')))]
            result[parameter_name] = self.wait_until_element(locator).text
        return result
