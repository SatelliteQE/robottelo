# -*- encoding: utf-8 -*-
"""Implements User groups UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, common_locators
from robottelo.common.constants import FILTER


class UserGroup(Base):
    """Implements the CRUD functions for User groups."""

    def create(self, name, users=None):
        """Creates new usergroup."""
        self.wait_until_element(locators['usergroups.new']).click()

        if self.wait_until_element(locators['usergroups.name']):
            self.find_element(locators['usergroups.name']).send_keys(name)
            self.configure_entity(users, FILTER['usergroup_user'])
            self.find_element(common_locators['submit']).click()
            self.wait_for_ajax()
        else:
            raise UIError(
                'Could not create new usergroup "{0}"'.format(name)
            )

    def search(self, name):
        """Searches existing usergroup from UI."""
        return self.search_entity(name, locators['usergroups.usergroup'])

    def delete(self, name, really):
        """Delete existing usergroup."""
        self.delete_entity(
            name,
            really,
            locators['usergroups.usergroup'],
            locators['usergroups.delete']
        )

    def update(self, old_name, new_name=None,
               users=None, new_users=None):
        """Update usergroup name and its users."""
        element = self.search(old_name)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                if self.wait_until_element(locators['usergroups.name']):
                    self.field_update('usergroups.name', new_name)
            self.configure_entity(
                users, FILTER['usergroup_user'], new_entity_list=new_users)
            self.find_element(common_locators['submit']).click()
            self.wait_for_ajax()
        else:
            raise UIError('Could not find usergroup "{0}"'.format(old_name))
