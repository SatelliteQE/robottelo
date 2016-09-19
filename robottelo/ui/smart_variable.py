# -*- encoding: utf-8 -*-
"""Implements Smart Variables UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class SmartVariable(Base):
    """Manipulates Smart Variables from UI"""

    search_key = 'key'

    def navigate_to_entity(self):
        """Navigate to Smart Variable entity page"""
        Navigator(self.browser).go_to_smart_variables()

    def _search_locator(self):
        """Specify locator for Smart Variable entity search procedure"""
        return locators['smart_variable.select_name']

    def _configure_variable(self, puppet_class=None, description=None,
                            key_type=None, default_value=None,
                            hidden_value=False, validator_type=None,
                            validator_rule=None, matcher=None,
                            matcher_priority=None,
                            matcher_merge_overrides=None,
                            matcher_merge_default=None,
                            matcher_merge_avoid=None):
        """Configuring Smart Variable parameters"""
        if puppet_class:
            self.assign_value(
                locators['smart_variable.puppet_class'], puppet_class)
        if description:
            self.assign_value(
                locators['smart_variable.description'], description)
        if key_type:
            self.assign_value(
                locators['smart_variable.key_type'], key_type)
        if default_value:
            self.assign_value(
                locators['smart_variable.default_value'], default_value)
        if validator_type or validator_rule:
            self.click(locators['smart_variable.optional_expander'])
            if validator_type:
                self.assign_value(
                    locators['smart_variable.validator_type'], validator_type)
            if validator_rule:
                self.assign_value(
                    locators['smart_variable.validator_rule'], validator_rule)
        if matcher_priority:
            self.assign_value(
                locators['smart_variable.matcher_priority'], matcher_priority)
        if matcher_merge_overrides is not None:
            self.assign_value(
                locators['smart_variable.merge_overrides'],
                matcher_merge_overrides
            )
        if matcher_merge_default is not None:
            self.assign_value(
                locators['smart_variable.merge_default'],
                matcher_merge_default
            )
        if matcher_merge_avoid is not None:
            self.assign_value(
                locators['smart_variable.avoid_duplicates'],
                matcher_merge_avoid
            )
        if matcher:
            self.add_matcher(matcher)
        if hidden_value is not None:
            self.assign_value(
                locators['smart_variable.hidden_value'], hidden_value)

    def create(self, name, puppet_class=None, description=None, key_type=None,
               default_value=None, hidden_value=False, validator_type=None,
               validator_rule=None, matcher=None, matcher_priority=None,
               matcher_merge_overrides=None, matcher_merge_default=None,
               matcher_merge_avoid=None):
        """Creates new Smart Variable from UI"""
        self.click(tab_locators['puppet_class.tab_smart_variable'])
        self.click(locators['smart_variable.new'])
        self.assign_value(locators['smart_variable.key'], name)
        self._configure_variable(
            description=description, key_type=key_type,
            default_value=default_value, hidden_value=hidden_value,
            validator_type=validator_type, validator_rule=validator_rule,
            matcher=matcher, matcher_priority=matcher_priority,
            matcher_merge_overrides=matcher_merge_overrides,
            matcher_merge_default=matcher_merge_default,
            matcher_merge_avoid=matcher_merge_avoid,
        )
        self.click(common_locators['submit'])

    def update(self, name, new_name=None, puppet_class=None, description=None,
               key_type=None, default_value=None, hidden_value=False,
               validator_type=None, validator_rule=None, matcher=None,
               matcher_priority=None, matcher_merge_overrides=None,
               matcher_merge_default=None, matcher_merge_avoid=None):
        """Updates existing Smart Variable from UI"""
        self.click(self.search(name))
        if new_name:
            self.assign_value(locators['smart_variable.key'], new_name)
        self._configure_variable(
            description=description, key_type=key_type,
            puppet_class=puppet_class, default_value=default_value,
            hidden_value=hidden_value, validator_type=validator_type,
            validator_rule=validator_rule, matcher_priority=matcher_priority,
            matcher=matcher, matcher_merge_overrides=matcher_merge_overrides,
            matcher_merge_default=matcher_merge_default,
            matcher_merge_avoid=matcher_merge_avoid,
        )
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes smart variable from UI"""
        self.delete_entity(
            name,
            really,
            locators['smart_variable.delete'],
        )

    def validate_smart_variable(self, name, field_name, field_value):
        """Checks if selected smart variable has necessary field value on the
        index pages

        :param str name: Name of Smart Variable to be validated
        :param str field_name: Smart Variable field that should be validated
            (e.g. 'puppet_class' or 'overrides_number')
        :param str field_value: Expected value for specified field
        """
        self.search(name)
        searched = self.wait_until_element(
            locators['smart_variable.table_value'] % field_value)
        if searched is None:
            raise UIError(
                'Smart Variable "{0}" field in the table has not "{1}" value.'
                .format(field_name, field_value)
            )
        else:
            return True

    def add_matcher(self, matcher_list):
        """Adding new matcher to Smart Variable

        :param matcher_list: List of matchers to be added to smart
            variable. Each element is a dictionary of next format:
            {
            'matcher_attribute': 'attr_type=attr_value',
            'matcher_value': 'value'
            }

        """
        for i, matcher in enumerate(matcher_list, start=1):
            self.click(locators['smart_variable.add_matcher'])
            matcher_attribute = matcher['matcher_attribute'].split('=')
            self.assign_value(
                locators['smart_variable.matcher_attribute_type'] % i,
                matcher_attribute[0]
            )
            self.assign_value(
                locators['smart_variable.matcher_attribute_value'] % i,
                matcher_attribute[1]
            )
            self.assign_value(
                locators['smart_variable.matcher_value'] % i,
                matcher['matcher_value']
            )

    def validate_checkbox(self, sv_name, checkbox_name):
        """Checks if specific smart variable checkbox is enabled or not

        :param str sv_name: Name of Smart Variable to be validated
        :param str checkbox_name: Name of Smart Variable check box that will be
            validated whether it is enabled or not (e.g. 'Merge overrides',
            'Merge default' or 'Avoid duplicates')
        :return bool: Return True if checkbox can be clicked and False
            otherwise
        """
        self.click(self.search(sv_name))
        locator_name = '.'.join((
            'smart_variable', (checkbox_name.lower()).replace(' ', '_')))
        return self.is_element_enabled(locators[locator_name])
