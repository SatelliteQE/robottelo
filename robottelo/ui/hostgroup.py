# -*- encoding: utf-8 -*-
"""Implements Host Group UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Hostgroup(Base):
    """Manipulates hostgroup from UI."""

    def navigate_to_entity(self):
        """Navigate to HostGroups entity page"""
        Navigator(self.browser).go_to_host_groups()

    def _search_locator(self):
        """Specify locator for HostGroups entity search procedure"""
        return locators['hostgroups.hostgroup']

    def _configure_hostsgroup_parameters(self, parameters_list):
        """Provide configuration capabilities for host group entity generic
        properties.
        All values should be passed in absolute correspondence to UI. For
        example, we need to choose a value from 'Content View' select list from
        'Host Group' tab and input root password in corresponding field
        from 'Operating System' tab, so next parameter list should be passed::

            [
                ['Host Group', 'Content View', 'Default Organization View'],
                ['Operating System', 'Root password', 'mynewpassword123'],
            ]

        """
        for tab_name, parameter_name, parameter_value in parameters_list:
            tab_locator = tab_locators['.tab_'.join((
                'hostgroup',
                (tab_name.lower()).replace(' ', '_')
            ))]
            self.click(tab_locator)
            locator_name = '.'.join((
                'hostgroups',
                (parameter_name.lower()).replace(' ', '_')
            ))
            if parameter_value is None:
                self.clear_entity_value(
                    locators['{}_clear'.format(locator_name)])
            else:
                self.assign_value(locators[locator_name], parameter_value)

    def _configure_taxonomies(self, locations=None, organizations=None):
        """Associate host group with organization or location"""
        if locations:
            self.configure_entity(
                locations,
                FILTER['hg_loc'],
                tab_locator=tab_locators['tab_loc'],
            )
        if organizations:
            self.configure_entity(
                organizations,
                FILTER['hg_org'],
                tab_locator=tab_locators['tab_org'],
            )

    def create(self, name, organizations=None, locations=None,
               parameters_list=None):
        """Creates a new hostgroup from UI."""
        self.click(locators['hostgroups.new'])
        self.assign_value(locators['hostgroups.name'], name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        if parameters_list is not None:
            self._configure_hostsgroup_parameters(parameters_list)
        self.click(common_locators['submit'])

    def update(self, name, new_name=None, organizations=None, locations=None,
               parameters_list=None):
        """Updates existing hostgroup from UI."""
        self.search_and_click(name)
        if new_name:
            self.assign_value(locators['hostgroups.name'], new_name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        if parameters_list is not None:
            self._configure_hostsgroup_parameters(parameters_list)
        self.click(common_locators['submit'])
