# -*- encoding: utf-8 -*-
"""Implements Smart Class Parameters UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class SmartClassParameter(Base):
    """Manipulates Smart class parameters from UI"""

    search_key = 'parameter'

    def navigate_to_entity(self):
        """Navigate to Smart class parameters entity page"""
        Navigator(self.browser).go_to_smart_class_parameters()

    def _search_locator(self):
        """Specify locator for Smart class parameters entity search
        procedure
        """
        return locators['sc_parameters.select_name']

    def search(self, sc_param_name, puppet_class):
        """Search for unique smart class parameter based on its name and puppet
        class parameter it is assigned to
        """
        return super(SmartClassParameter, self).search(
            sc_param_name,
            _raw_query='parameter = {0} and puppetclass_name = {1}'.format(
                sc_param_name, puppet_class)
        )

    def update(self, name, puppet_class, change_puppet_class=False,
               description=None, override=None, key_type=None,
               default_value=None, puppet_default=None, hidden_value=None,
               validator_type=None, validator_rule=None, matcher=None,
               matcher_priority=None, matcher_merge_overrides=None,
               matcher_merge_default=None, matcher_merge_avoid=None):
        """Updates existing Smart Class Parameter from UI"""
        self.click(self.search(name, puppet_class))
        if description:
            self.assign_value(
                locators['sc_parameters.description'], description)
        if change_puppet_class:
            self.assign_value(
                locators['sc_parameters.puppetclass'], puppet_class)
        if override is not None:
            self.assign_value(
                locators['sc_parameters.override'], override)
        if puppet_default is not None:
            self.assign_value(
                locators['sc_parameters.puppet_default'], puppet_default)
        if key_type:
            self.assign_value(
                locators['sc_parameters.key_type'], key_type)
        if default_value is not None:
            self.assign_value(
                locators['sc_parameters.default_value'], default_value)
        if validator_type or validator_rule:
            self.click(locators['sc_parameters.optional_expander'])
            if validator_type:
                self.assign_value(
                    locators['sc_parameters.validator_type'], validator_type)
            if validator_rule:
                self.assign_value(
                    locators['sc_parameters.validator_rule'], validator_rule)
        if matcher_priority:
            self.assign_value(
                locators['sc_parameters.matcher_priority'], matcher_priority)
        if matcher_merge_overrides is not None:
            self.assign_value(
                locators['sc_parameters.merge_overrides'],
                matcher_merge_overrides
            )
        if matcher_merge_default is not None:
            self.assign_value(
                locators['sc_parameters.merge_default'],
                matcher_merge_default
            )
        if matcher_merge_avoid is not None:
            self.assign_value(
                locators['sc_parameters.avoid_duplicates'],
                matcher_merge_avoid
            )
        if matcher:
            self.add_matcher(matcher)
        if hidden_value is not None:
            self.assign_value(
                locators['sc_parameters.hidden_value'], hidden_value)
        self.click(common_locators['submit'])

    def add_matcher(self, matcher_list):
        """Adding new matcher to Smart Variable

        :param matcher_list: List of matchers to be added to smart class
            parameter. Each element is a dictionary of next format:
            {
            'matcher_attribute': 'attr_type=attr_value',
            'matcher_value': 'value',
            (optional) 'matcher_puppet_default': True
            }

        """
        for i, matcher in enumerate(matcher_list, start=1):
            self.click(locators['sc_parameters.add_matcher'])
            matcher_attribute = matcher['matcher_attribute'].split('=')
            strategy, value = locators['sc_parameters.matcher_attribute_type']
            self.assign_value(
                (strategy, value % i), matcher_attribute[0])
            strategy, value = locators['sc_parameters.matcher_attribute_value']
            self.assign_value(
                (strategy, value % i), matcher_attribute[1])
            strategy, value = locators['sc_parameters.matcher_value']
            self.assign_value(
                (strategy, value % i), matcher['matcher_value'])
            if 'matcher_puppet_default' in matcher.keys():
                strategy, value = locators[
                    'sc_parameters.matcher_puppet_default']
                self.assign_value(
                    (strategy, value % i), matcher['matcher_puppet_default'])

    def validate_smart_class_parameter(
            self, name, puppet_class, field_name, field_value):
        """Checks if selected smart class parameter has necessary field values
        on the index page

        :param str name: Name of Smart Class Parameter to be validated
        :param str puppet_class: Name of puppet class Smart Class Parameter
            assigned to
        :param str field_name: Smart Class Parameter field that should be
            validated (e.g. 'puppet_class' or 'overrides_number')
        :param str field_value: Expected value for specified field
        """
        self.search(name, puppet_class)
        strategy, value = locators['sc_parameters.table_value']
        searched = self.wait_until_element((strategy, value % field_value))
        if searched is None:
            raise UIError(
                'Smart Class Parameter "{0}" field in the table has not "{1}" '
                'value.'.format(field_name, field_value)
            )
        else:
            return True

    def fetch_default_value(self, name, puppet_class, hidden=False):
        """Get default value for specific Smart Class Parameter"""
        self.click(self.search(name, puppet_class))
        locator = self.wait_until_element(
            locators['sc_parameters.default_value'])
        return locator.get_attribute('value') if hidden else locator.text

    def fetch_matcher_values(self, name, puppet_class, matchers_count):
        """Get list of values for specified number of Smart Class Parameter
        matchers
        """
        strategy, value = locators['sc_parameters.matcher_value']
        self.click(self.search(name, puppet_class))
        return [
            self.wait_until_element((strategy, value % (i+1))).text
            for i
            in range(0, matchers_count)
        ]
