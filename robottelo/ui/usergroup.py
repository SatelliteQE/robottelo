# -*- encoding: utf-8 -*-
"""Implements User groups UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class UserGroup(Base):
    """Implements the CRUD functions for User groups."""

    def navigate_to_entity(self):
        """Navigate to Usergroup entity page"""
        Navigator(self.browser).go_to_user_groups()

    def _search_locator(self):
        """Specify locator for Usergroup entity search procedure"""
        return locators['usergroups.usergroup']

    def create(self, name, users=None, roles=None,
               ext_usergrp=None, ext_authsourceid=None):
        """Creates new usergroup."""
        self.click(locators['usergroups.new'])

        if self.wait_until_element(locators['usergroups.name']) is None:
            raise UIError('Could not create new usergroup "{0}"'.format(name))
        self.find_element(locators['usergroups.name']).send_keys(name)
        self.configure_entity(users, FILTER['usergroup_user'])
        if roles:
            self.click(tab_locators['usergroups.tab_roles'])
            if "admin" in roles:
                self.click(locators['usergroups.admin'])
            else:
                self.configure_entity(roles, FILTER['usergroup_role'])
        if ext_usergrp:
            self.click(tab_locators['usergroups.tab_external'])
            self.click(locators['usergroups.addexternal_usergrp'])
            self.text_field_update(
                locators['usergroups.ext_usergroup_name'],
                ext_usergrp
            )
            self.assign_value(
                locators['usergroups.ext_authsource_id'], ext_authsourceid)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Delete existing usergroup."""
        self.delete_entity(
            name,
            really,
            locators['usergroups.delete'],
        )

    def update(self, old_name, new_name=None, users=None, new_users=None,
               roles=None, new_roles=None, entity_select=None):
        """Update usergroup name and its users."""
        if roles is None:
            roles = []
        if new_roles is None:
            new_roles = []
        self.click(self.get_entity(old_name))
        if new_name and self.wait_until_element(locators['usergroups.name']):
            self.field_update('usergroups.name', new_name)
        self.configure_entity(
            users, FILTER['usergroup_user'], new_entity_list=new_users)
        if roles or new_roles:
            self.click(tab_locators['usergroups.tab_roles'])
            if "admin" in roles or "admin" in new_roles:
                self.click(locators['usergroups.admin'])
            else:
                self.configure_entity(
                    entity_list=roles,
                    new_entity_list=new_roles,
                    filter_key=FILTER['usergroup_role'],
                    entity_select=entity_select,
                )
        self.click(common_locators['submit'])

    def refresh_ext_group(self, name, ext_group_name):
        """Refresh external usergroup entity"""
        self.click(self.get_entity(name))
        self.click(tab_locators['usergroups.tab_external'])
        strategy, value = locators['usergroups.ext_refresh']
        self.click((strategy, value % ext_group_name))
