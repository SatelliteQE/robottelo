# -*- encoding: utf-8 -*-
"""Implements User UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class User(Base):
    """Implements CRUD functions from UI."""

    def _configure_user(self, roles=None, locations=None, organizations=None,
                        new_locations=None, new_roles=None,
                        new_organizations=None, default_org=None,
                        default_loc=None, select=None):
        """Configures different entities of selected User."""
        loc = tab_locators

        if roles or new_roles:
            self.configure_entity(
                roles,
                FILTER['user_role'],
                tab_locator=loc['users.tab_roles'],
                new_entity_list=new_roles,
                entity_select=select
            )
        if locations or new_locations:
            self.configure_entity(
                locations,
                FILTER['user_location'],
                tab_locator=loc['users.tab_locations'],
                new_entity_list=new_locations,
                entity_select=select
            )
            if default_loc:
                loc_element = self.find_element(locators['users.default_loc'])
                Select(loc_element).select_by_visible_text(default_loc)
        if organizations or new_organizations:
            self.configure_entity(
                organizations,
                FILTER['user_org'],
                tab_locator=loc['users.tab_organizations'],
                new_entity_list=new_organizations,
                entity_select=select,
            )
            if default_org:
                org_element = self.find_element(locators['users.default_org'])
                Select(org_element).select_by_visible_text(default_org)

    def create(self, username=None, email=None, password1=None,
               password2=None, authorized_by='INTERNAL',
               locale=None, first_name=None, last_name=None,
               roles=None, locations=None, organizations=None,
               edit=False, default_org=None, default_loc=None, select=True):
        """Create new user from UI."""
        self.click(locators['users.new'])
        if self.wait_until_element(locators['users.username']):
            self.field_update('users.username', username)
        if first_name:
            self.field_update('users.firstname', first_name)
        if last_name:
            self.field_update('users.lastname', last_name)
        if self.wait_until_element(locators['users.authorized_by']):
            Select(
                self.find_element(locators['users.authorized_by'])
            ).select_by_visible_text(authorized_by)
        # The following fields are not available via LDAP auth
        if self.wait_until_element(locators['users.email']):
            self.field_update('users.email', email)
        # If authorized_by is None, click submit.
        # For use in negative create tests.
        if authorized_by:
            if self.wait_until_element(locators['users.password']):
                self.field_update('users.password', password1)
            if self.wait_until_element(
                    locators['users.password_confirmation']):
                self.field_update('users.password_confirmation', password2)
            if locale:
                Select(
                    self.find_element(locators['users.language'])
                ).select_by_value(locale)
            if edit:
                self._configure_user(
                    roles=roles,
                    locations=locations,
                    organizations=organizations,
                    default_org=default_org,
                    default_loc=default_loc,
                    select=select
                )
        self.click(common_locators['submit'])

    def search(self, name, search_key):
        """Searches existing user from UI."""
        Navigator(self.browser).go_to_users()
        return self.search_entity(
            name, locators['users.user'], search_key=search_key)

    def delete(self, name, search_key, really=True):
        """Deletes existing user from UI."""
        self.delete_entity(
            name,
            really,
            locators['users.user'],
            locators['users.delete'],
            search_key=search_key,
        )

    def update(self, search_key, username, new_username=None,
               email=None, password=None,
               first_name=None, last_name=None, locale=None,
               roles=None, new_roles=None, locations=None,
               new_locations=None, organizations=None,
               new_organizations=None, default_org=None,
               default_loc=None, select=False):
        """Update username, email, password, firstname, lastname and locale
        from UI

        """
        element = self.search(username, search_key)

        if element is None:
            raise UIError(
                'Unable to find the username "{0}" for update.'
                .format(username)
            )

        element.click()
        self.wait_for_ajax()
        if new_username:
            self.field_update('users.username', new_username)
        if email:
            self.field_update('users.email', email)
        if first_name:
            self.field_update('users.firstname', first_name)
        if last_name:
            self.field_update('users.lastname', last_name)
        if locale:
            Select(
                self.find_element(locators['users.language'])
            ).select_by_value(locale)
        if password:
            self.field_update('users.password', password)
            self.field_update('users.password_confirmation', password)
        self._configure_user(
            roles=roles,
            new_roles=new_roles,
            locations=locations,
            new_locations=new_locations,
            organizations=organizations,
            new_organizations=new_organizations,
            default_org=default_org,
            default_loc=default_loc,
            select=select
        )
        self.click(common_locators['submit'])

    def admin_role_to_user(self, username, search_key='login'):
        """Checks if selected user has Administrator privileges otherwise
        assign it to user.

        """
        element = self.search(username, search_key)

        if element is None:
            raise UINoSuchElementError(
                'Unable to find the username "{0}".'.format(username)
            )

        element.click()
        self.wait_for_ajax()
        self.click(tab_locators['users.tab_roles'])
        admin_role_locator = locators['users.admin_role']
        is_admin_role_selected = self.find_element(
            admin_role_locator).is_selected()
        if not is_admin_role_selected:
            self.click(admin_role_locator)
            self.click(common_locators['submit'])
            is_admin_role_selected = True
        return is_admin_role_selected
