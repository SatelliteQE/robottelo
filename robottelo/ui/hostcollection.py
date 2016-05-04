# -*- encoding: utf-8 -*-
"""Implements Host Collection UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class HostCollection(Base):
    """Provides the CRUD functionality for Host Collection."""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Host Collection entity page"""
        Navigator(self.browser).go_to_host_collections()

    def _search_locator(self):
        """Specify locator for Host Collection entity search procedure"""
        return locators['hostcollection.select_name']

    def create(self, name, limit=None, description=None):
        """Creates new Host Collection from UI."""
        self.click(locators['hostcollection.new'])

        if self.wait_until_element(common_locators['name']) is None:
            raise UIError(
                u'Could not create new host collection "{0}"'.format(name)
            )

        self.text_field_update(common_locators['name'], name)
        if limit:
            self.set_limit(limit)
        if description:
            self.text_field_update(
                common_locators['description'], description)
        self.click(common_locators['create'])

    def update(self, name, new_name=None, description=None, limit=None):
        """Updates an existing Host Collection."""
        element = self.search(name)
        if element is None:
            raise UIError(
                u'Could not find host collection "{0}" to update'.format(name))

        element.click()
        self.wait_for_ajax()
        if new_name:
            self.edit_entity(
                locators['hostcollection.edit_name'],
                locators['hostcollection.edit_name_text'],
                new_name,
                locators['hostcollection.save_name'],
            )
        if description:
            self.edit_entity(
                locators['hostcollection.edit_description'],
                locators['hostcollection.edit_description_text'],
                description,
                locators['hostcollection.save_description']
            )
        if limit:
            self.click(locators['hostcollection.edit_limit'])
            self.set_limit(limit)
            if self.wait_until_element(
                    locators['hostcollection.save_limit']).is_enabled():
                self.click(locators['hostcollection.save_limit'])
            else:
                raise ValueError(
                    'Please update content host limit with valid integer '
                    'value'
                )

    def validate_field_value(self, name, field_name, field_value):
        """Validate whether corresponding Host Collection field has expected
        value

        :param str name: Host Collection name
        :param str field_name: Field to be validated (supported fields: 'name',
            'description', 'limit')
        :param str field_value: Expected field value
        :return bool result: Return True in case field contains expected value
            and False otherwise

        """
        element = self.search(name)
        if element is None:
            raise UIError(
                u'Could not find host collection "{0}" to verify'.format(name))
        element.click()
        self.wait_for_ajax()
        strategy, value = locators[
            'hostcollection.{0}_field'.format(field_name)]
        return self.wait_until_element((strategy, value % field_value))

    def delete(self, name, really=True):
        """Deletes an existing Host Collection entity."""
        self.delete_entity(
            name,
            really,
            locators['hostcollection.remove'],
        )

    def copy(self, name, new_name):
        """Copies an existing Host Collection entity"""
        element = self.search(name)
        if element is None:
            raise UIError(
                u'Could not find host collection "{0}" to copy'.format(name))

        element.click()
        self.wait_for_ajax()
        self.edit_entity(
            locators['hostcollection.copy'],
            locators['hostcollection.copy_name'],
            new_name,
            locators['hostcollection.copy_create'],
        )

    def add_host(self, name, host_name):
        """Add content host to existing Host Collection entity."""
        # find host collection
        host_collection = self.search(name)
        if host_collection is None:
            raise UIError(
                u'Could not find host collection {0}'.format(name))
        host_collection.click()
        self.wait_for_ajax()
        self.click(tab_locators['hostcollection.hosts'])
        self.click(tab_locators['hostcollection.tab_host_add'])
        strategy, value = locators['hostcollection.select_host']
        self.click((strategy, value % host_name))
        self.click(locators['hostcollection.add_host'])
        self.click(tab_locators['hostcollection.tab_host_remove'])
        element = self.wait_until_element(
            (strategy, value % host_name), timeout=8)
        if element is None:
            raise UIError("Adding host {0} is failed".format(host_name))
