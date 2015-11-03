# -*- encoding: utf-8 -*-
"""Implements Host Group UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Hostgroup(Base):
    """Manipulates hostgroup from UI."""

    def create(self, name, parent=None, environment=None, content_source=None,
               puppet_ca=None, puppet_master=None):
        """Creates a new hostgroup from UI."""
        self.click(locators['hostgroups.new'])
        if not self.wait_until_element(locators['hostgroups.name']):
            raise UIError('Could not create new hostgroup.')
        self.find_element(locators['hostgroups.name']).send_keys(name)
        if parent:
            self.select(locators['hostgroups.parent'], parent)
        if environment:
            self.select(locators['hostgroups.environment'], environment)
        if content_source:
            self.select(locators['hostgroups.content_source'], content_source)
        if puppet_ca:
            self.select(locators['hostgroups.puppet_ca'], puppet_ca)
        if puppet_master:
            self.select(locators['hostgroups.puppet_master'], puppet_master)
        self.click(common_locators['submit'])

    def search(self, name, element_locator=None, search_key=None,
               katello=False, button_timeout=15, result_timeout=15):
        """Searches existing hostgroup from UI."""
        Navigator(self.browser).go_to_host_groups()
        return super(Hostgroup, self).search(
            name,
            locators['hostgroups.hostgroup'] or element_locator,
            search_key=search_key,
            katello=katello,
            button_timeout=button_timeout,
            result_timeout=result_timeout,
        )

    def delete(self, name, really=True):
        """Deletes existing hostgroup from UI."""
        Navigator(self.browser).go_to_host_groups()
        self.delete_entity(
            name,
            really,
            locators['hostgroups.hostgroup'],
            locators['hostgroups.delete'],
            drop_locator=locators['hostgroups.dropdown'],
        )

    def update(self, name, new_name=None, parent=None, environment=None):
        """Updates existing hostgroup from UI."""
        element = self.search(name)
        if not element:
            raise UIError('Could not find hostgroup "{0}"'.format(name))
        element.click()
        self.wait_for_ajax()
        if parent:
            self.select(locators['hostgroups.parent'], parent)
        if environment:
            self.select(locators['hostgroups.environment'], environment)
        if new_name:
            self.text_field_update(locators['hostgroups.name'], new_name)
        self.click(common_locators['submit'])
