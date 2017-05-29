# -*- encoding: utf-8 -*-
"""Implements User groups UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base
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
        self.assign_value(locators['usergroups.name'], name)
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
            self.assign_value(
                locators['usergroups.ext_usergroup_name'],
                ext_usergrp
            )
            self.assign_value(
                locators['usergroups.ext_authsource_id'], ext_authsourceid)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name=None, users=None, new_users=None,
               roles=None, new_roles=None, entity_select=None):
        """Update usergroup name and its users."""
        if roles is None:
            roles = []
        if new_roles is None:
            new_roles = []
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['usergroups.name'], new_name)
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
        self.search_and_click(name)
        self.click(tab_locators['usergroups.tab_external'])
        self.click(locators['usergroups.ext_refresh'] % ext_group_name)
