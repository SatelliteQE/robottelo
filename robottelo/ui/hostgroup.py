# -*- encoding: utf-8 -*-
"""Implements Host Group UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Hostgroup(Base):
    """Manipulates hostgroup from UI."""

    def create(self, name, parent=None, environment=None, content_source=None,
               content_view=None, puppet_ca=None, puppet_master=None,
               oscap_capsule=None, activation_keys=None):
        """Creates a new hostgroup from UI."""
        self.click(locators['hostgroups.new'])
        self.assign_value(locators['hostgroups.name'], name)
        if parent:
            self.assign_value(locators['hostgroups.parent'], parent)
        if environment:
            self.assign_value(locators['hostgroups.environment'], environment)
        if content_source:
            self.assign_value(
                locators['hostgroups.content_source'], content_source)
        if content_view:
            self.assign_value(
                locators['hostgroups.content_view'], content_view)
        if puppet_ca:
            self.assign_value(locators['hostgroups.puppet_ca'], puppet_ca)
        if puppet_master:
            self.assign_value(
                locators['hostgroups.puppet_master'], puppet_master)
        if oscap_capsule:
            self.assign_value(
                locators['hostgroups.oscap_capsule'], oscap_capsule)
        if activation_keys:
            self.click(tab_locators['hostgroup.activation_keys'])
            self.assign_value(
                locators['hostgroups.activation_keys'], activation_keys)
        self.click(common_locators['submit'])

    def navigate_to_entity(self):
        """Navigate to HostGroups entity page"""
        Navigator(self.browser).go_to_host_groups()

    def _search_locator(self):
        """Specify locator for HostGroups entity search procedure"""
        return locators['hostgroups.hostgroup']

    def delete(self, name, really=True):
        """Deletes existing hostgroup from UI."""
        self.delete_entity(
            name,
            really,
            common_locators['delete_button'],
            drop_locator=locators['hostgroups.dropdown'],
        )

    def update(self, name, new_name=None, parent=None, environment=None):
        """Updates existing hostgroup from UI."""
        self.search_and_click(name)
        if parent:
            self.assign_value(locators['hostgroups.parent'], parent)
        if environment:
            self.assign_value(locators['hostgroups.environment'], environment)
        if new_name:
            self.assign_value(locators['hostgroups.name'], new_name)
        self.click(common_locators['submit'])
