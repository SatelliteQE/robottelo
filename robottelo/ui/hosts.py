"""Utilities to manipulate hosts via UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Hosts(Base):
    """Provides the CRUD functionality for Host."""

    def navigate_to_entity(self):
        """Navigate to Hosts entity page"""
        Navigator(self.browser).go_to_hosts()

    def _search_locator(self):
        """Specify locator for Hosts entity search procedure"""
        return locators['host.select_name']

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
                self.assign_value(
                    common_locators['select_list_search_box'],
                    parameter_value.split(' (')[0]
                )
                # selecting compute resource by its full name (with parenthesis
                # part)
                self.click(
                    common_locators['entity_select_list'] % parameter_value)
                continue
            elif parameter_name == 'Puppet Environment':
                # Make sure 'inherit' button is not pressed before selecting
                # puppet environment, as otherwise 'Puppet Environment'
                # dropdown will be disabled
                inherit = self.wait_until_element(
                    locators.host.inherit_puppet_environment)
                if 'active' in inherit.get_attribute('class'):
                    self.click(inherit)
            elif parameter_name == 'Compute profile':
                inherit = self.wait_until_element(
                    locators.host.inherit_compute_profile)
                if 'active' in inherit.get_attribute('class'):
                    self.click(inherit)
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
            # send_keys() can't send left parenthesis (see
            # SeleniumHQ/selenium#674), which is a part of network type name
            # (e.g. 'Physical (Bridge)')
            if parameter_name == 'Network type' and ' (' in parameter_value:
                self.click(param_locator)
                # typing network type name without parenthesis part
                self.assign_value(
                    common_locators['select_list_search_box'],
                    parameter_value.split(' (')[0]
                )
                # selecting network type by its full name (with parenthesis
                # part)
                self.click(
                    common_locators['entity_select_list'] % parameter_value)
                continue
            self.assign_value(param_locator, parameter_value)
        self.click(locators['host.save_interface'])

    def _configure_provisioning_method(self, method):
        """Provide configuration capabilities for host to be created using
        provisioning methods. Eg.Boot disk based, Network Based, Image Based
        """
        self.click(tab_locators['host.tab_operating_system'])
        if method == 'bootdisk':
            self.click(tab_locators['operatingsys.tab_provision_bootdisk'])
        elif method == 'network':
            self.click(tab_locators['operatingsys.tab_provision_network'])
        elif method == 'image':
            self.click(tab_locators['operatingsys.tab_provision_images'])

    def _configure_puppet_modules(self, puppet_modules_list):
        """Provide configuration capabilities for host entity puppet classes
        tab.
        """
        self.click(tab_locators['host.tab_puppet_classes'])
        for puppet_module in puppet_modules_list:
            self.click(locators['host.select_puppetmodule'] % puppet_module)
            self.click(locators['host.select_puppetclass'] % puppet_module)

    def _add_host_parameters(self, parameters_list):
        """Add new host parameters for 'parameters' tab. Example::

        host_parameters=[['test01', 'value01'], ['test02', 'value02'],
        ['test03', 'value03']]

        """
        self.click(tab_locators['host.tab_params'])
        index = 1
        for parameter_name, parameter_value in parameters_list:
            self.click(locators['host.add_new_host_parameter'])
            self.assign_value(
                locators['host.host_parameter_name'] % index, parameter_name)
            self.assign_value(
                locators['host.host_parameter_value'] % index, parameter_value)
            index += 1

    def create(self, name, parameters_list=None, puppet_classes=None,
               interface_parameters=None, host_parameters=None,
               provisioning_method=None):
        """Creates a host."""
        self.click(locators['host.new'])
        self.assign_value(locators['host.name'], name)
        if parameters_list is not None:
            self._configure_hosts_parameters(parameters_list)
        if puppet_classes is not None:
            self._configure_puppet_modules(puppet_classes)
        if interface_parameters is not None:
            self.click(tab_locators['host.tab_interfaces'])
            self.click(locators['host.edit_default_interface'])
            self._configure_interface_parameters(interface_parameters)
        if host_parameters is not None:
            self._add_host_parameters(host_parameters)
        if provisioning_method is not None:
            self.click(tab_locators['host.tab_operating_system'])
            self._configure_provisioning_method(provisioning_method)
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
            self.assign_value(locators['host.name'], new_name)
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
        :raises TypeError: in case neither `interface_id` nor `interface_mac`
            were passed
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
        self.click(locators['host.delete_interface'] % identifier)
        self.click(common_locators['submit'])

    def update_host_bulkactions(
            self, hosts=None, action=None, parameters_list=None):
        """Updates host via bulkactions

        :param hosts: List of hosts that should be selected for action
        :param action: Specify exact action to perform according to UI list.
            At that moment we support next actions::
            - Assign Organization
            - Run Job
            - Delete Hosts
            - Change Group
            - Change Environment
        :param parameters_list: List of parameters that are needed for the
            dialogs that go after necessary action was selected. For example::

            [{'organization': 'My_org01'}]
            [{'command': 'ls'}]
        """
        self.navigate_to_entity()
        for host in hosts:
            self.click(locators['host.checkbox'] % host)
        self.click(locators['host.select_action_list'])
        self.click(locators['host.select_action'] % action)
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
                if action == 'Change Group':
                    self.assign_value(
                        locators['host.select_host_group'],
                        parameter['host_group_name']
                    )
                    self.click(locators['host.bulk_submit'])
                if action == 'Change Environment':
                    self.assign_value(
                        locators['host.select_environment'],
                        parameter['puppet_env_name']
                    )
                    self.click(locators['host.bulk_submit'])
                if action == 'Assign Compliance Policy':
                    self.click(locators['host.select_policy'])
                    self.assign_value(
                        locators['host.select_policy'],
                        parameter['policy']
                    )
                    self.click(locators['host.bulk_submit'])

    def get_yaml_output(self, name):
        """Return YAML output for specific host

        :param str name: Name of Host to read information from
        """
        self.search_and_click(name)
        self.click(locators['host.yaml_button'])
        output = self.wait_until_element(locators['host.yaml_output']).text
        self.browser.back()
        self.wait_for_ajax()
        return output

    def get_smart_variable_value(self, host_name, sv_name):
        """Return smart variable value element for specific host

        :param str host_name: Name of Host to get smart variable information
            from
        :param str sv_name: Name of Smart Variable to be read
        """
        self.click(self.search(host_name))
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_params'])
        return self.wait_until_element(
            locators['host.smart_variable_value'] % sv_name)

    def set_smart_variable_value(self, host_name, sv_name, sv_value,
                                 override=True):
        """Set smart variable value for specific host

        :param str host_name: Name of Host where smart variable value should be
            modified
        :param str sv_name: Name of Smart Variable to be modified
        :param str sv_value: Value of Smart Variable that should be set
        :param bool override: Specify whether it is expected to override smart
            value or just edit its value
        """
        self.search_and_click(host_name)
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_params'])
        if override:
            self.click(locators['host.smart_variable_override'] % sv_name)
        self.assign_value(
            locators['host.smart_variable_value'] % sv_name, sv_value)
        self.click(common_locators['submit'])

    def fetch_global_parameters(self, name, domain_name):
        """Fetches hosts global parameters. Returns a list of name-value pairs.
        """
        host = self.search(u'{0}.{1}'.format(name, domain_name))
        self.click(host)
        self.click(locators['host.edit'])
        self.click(tab_locators['host.tab_params'])
        params = self.find_elements(
            locators['host.global_parameter_name'] % '')
        result = []
        for param in params:
            param_name = param.text
            param_value = self.find_element(
                locators['host.global_parameter_value'] % param_name).text
            result.append((param_name, param_value))
        return result

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

    def get_host_properties(self, host, parameters_list):
        """Get necessary host properties by theirs names"""
        self.search_and_click(host)
        result = {}
        for parameter_name in parameters_list:
            locator = locators['.property_'.join(
                ('host', (parameter_name.lower()).replace(' ', '_')))]
            result[parameter_name] = self.wait_until_element(locator).text
        return result
