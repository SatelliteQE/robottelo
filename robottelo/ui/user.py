# -*- encoding: utf-8 -*-
"""Implements User UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class User(Base):
    """Implements CRUD functions from UI."""

    search_key = 'login'

    def navigate_to_entity(self):
        """Navigate to User entity page"""
        Navigator(self.browser).go_to_users()

    def _search_locator(self):
        """Specify locator for User entity search procedure"""
        return locators['users.user']

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
                self.select(locators['users.default_loc'], default_loc)
        if organizations or new_organizations:
            self.configure_entity(
                organizations,
                FILTER['user_org'],
                tab_locator=loc['users.tab_organizations'],
                new_entity_list=new_organizations,
                entity_select=select,
            )
            if default_org:
                self.select(locators['users.default_org'], default_org)

    def create(self, username=None, email=None, timezone=None, password1=None,
               password2=None, authorized_by='INTERNAL', locale=None,
               first_name=None, last_name=None, roles=None, admin=False,
               locations=None, organizations=None, edit=False,
               default_org=None, default_loc=None, select=True, submit=True):
        """Create new user from UI."""
        self.click(locators['users.new'])
        self.text_field_update(locators['users.username'], username)
        if first_name:
            self.text_field_update(locators['users.firstname'], first_name)
        if last_name:
            self.text_field_update(locators['users.lastname'], last_name)
        if email:
            self.text_field_update(locators['users.email'], email)
        if timezone:
            self.select(locators['users.timezone_dropdown'], timezone)
        if locale:
            self.select(locators['users.language_dropdown'], locale)
        if authorized_by:
            self.select(locators['users.authorized_by'], authorized_by)
            if self.wait_until_element(locators['users.password']):
                self.field_update('users.password', password1)
            if self.wait_until_element(
                    locators['users.password_confirmation']):
                self.field_update('users.password_confirmation', password2)
        if edit:
            self._configure_user(
                roles=roles,
                locations=locations,
                organizations=organizations,
                default_org=default_org,
                default_loc=default_loc,
                select=select
            )
        if admin:
            self.click(tab_locators['users.tab_roles'])
            self.click(locators['users.admin_role'])
        if submit:
            self.click(common_locators['submit'])
        else:
            self.click(common_locators['cancel_form'])

    def delete(self, name, really=True):
        """Deletes existing user from UI."""
        self.delete_entity(
            name,
            really,
            locators['users.delete'],
        )

    def update(self, username, new_username=None, email=None,
               new_password=None, password_confirmation=None, first_name=None,
               last_name=None, locale=None, roles=None, timezone=None,
               new_roles=None, locations=None, new_locations=None,
               organizations=None, new_organizations=None, default_org=None,
               default_loc=None, select=False, authorized_by=None,
               submit=True):
        """Update user related fields from UI"""
        self.click(self.get_entity(username))
        if new_username:
            self.field_update('users.username', new_username)
        if email:
            self.field_update('users.email', email)
        if first_name:
            self.field_update('users.firstname', first_name)
        if last_name:
            self.field_update('users.lastname', last_name)
        if locale:
            self.select(locators['users.language_dropdown'], locale)
        if timezone:
            self.select(locators['users.timezone_dropdown'], timezone)
        if authorized_by:
            self.select(locators['users.authorized_by'], authorized_by)
        if new_password:
            self.text_field_update(locators['users.password'], new_password)
        if password_confirmation:
            self.text_field_update(
                locators['users.password_confirmation'], password_confirmation)
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
        if submit:
            self.click(common_locators['submit'])
        else:
            self.click(common_locators['cancel_form'])

    def user_admin_role_toggle(self, username, is_admin=True):
        """Checks if selected user has Administrator privileges according to
        expected state and assign/unassign them otherwise
        """
        self.click(self.get_entity(username))
        self.click(tab_locators['users.tab_roles'])
        admin_role_locator = locators['users.admin_role']
        is_admin_role_selected = self.find_element(
            admin_role_locator).is_selected()
        if is_admin_role_selected != is_admin:
            self.click(admin_role_locator)
            self.click(common_locators['submit'])
            is_admin_role_selected = is_admin
        return is_admin_role_selected

    def validate_user(
            self, username, field_name, field_value, validate_index_page=True):
        """Checks if selected user has necessary field values on the index and
        edit pages

        :param str username: Username of the user to be validated
        :param str field_name: User field that should be validated (e.g.
            'firstname' or 'lastname')
        :param str field_value: Expected value for specified field
        :param bool validate_index_page: Specify whether we like to validate
            user field value not only on user edit screen, but on index page
            (where we have search functionality and table with all users). Not
            all fields values present in the table, so we have specify that
            parameter explicitly
        """
        element = self.get_entity(username)
        if element is None:
            raise UINoSuchElementError(
                'Unable to find the username "{0}".'.format(username)
            )
        if validate_index_page:
            strategy, value = locators['users.table_value']
            searched = self.wait_until_element(
                (strategy, value % field_value))
            if searched is None:
                raise UINoSuchElementError(
                    'User "{0}" field in the table has not "{1}" value.'
                    .format(field_name, field_value)
                )

        self.click(element)
        if (self.wait_until_element(
                locators['users.' + field_name]
                ).get_attribute('value') != field_value and
            self.wait_until_element(locators[
                'users.' + field_name]).text != field_value):
            raise UIError(
                'User "{0}" field in the edit screen has not "{1}" value.'
                .format(field_name, field_value)
            )
