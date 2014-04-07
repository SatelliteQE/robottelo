# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements User UI
"""

from robottelo.common.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class User(Base):
    """
    Implements CRUD functions from UI
    """


    def _configure_user(self, roles=None, locations=None, organizations=None,
                        new_locations=None, new_roles=None,
                        new_organizations=None,
                        select=None):
        """
        Configures different entities of selected User
        """

        loc = tab_locators

        if roles or new_roles:
            self.configure_entity(roles, FILTER['user_role'],
                                  tab_locator=loc["users.tab_roles"],
                                  new_entity_list=new_roles,
                                  entity_select=select)
        if locations or new_locations:
            self.configure_entity(locations, FILTER['user_location'],
                                  tab_locator=loc["user.tab_locations"],
                                  new_entity_list=new_locations,
                                  entity_select=select)
        if organizations or new_organizations:
            self.configure_entity(organizations, FILTER['user_org'],
                                  tab_locator=loc["users.tab_organizations"],
                                  new_entity_list=new_organizations,
                                  entity_select=select)

    def create(self, username, email=None, password1=None,
               password2=None, authorized_by="INTERNAL",
               locale=None, first_name=None, last_name=None,
               roles=None, locations=None, organizations=None,
               edit=False, select=True):
        """
        Create new user from UI
        """

        if self.wait_until_element(locators["users.new"]):
            self.wait_until_element(locators["users.new"]).click()
            if self.wait_until_element(locators["users.username"]):
                self.field_update("users.username", username)
            if first_name:
                self.field_update("users.firstname", first_name)
            if last_name:
                self.field_update("users.lastname", last_name)
            if self.wait_until_element(locators["users.authorized_by"]):
                Select(self.find_element(locators["users.authorized_by"])
                       ).select_by_visible_text(authorized_by)
            # The following fields are not available via LDAP auth
            if self.wait_until_element(locators["users.email"]):
                self.field_update("users.email", email)
            # If authorized_by is None, click submit.
            # For use in negative create tests.
            if not authorized_by:
                self.wait_until_element(common_locators["submit"]).click()
                self.wait_for_ajax()
            else:
                if self.wait_until_element(locators["users.password"]):
                    self.field_update("users.password", password1)
                if self.wait_until_element(locators
                                           ["users.password_confirmation"]):
                    self.field_update("users.password_confirmation", password2)
                if locale:
                    Select(self.find_element(locators["users.language"]
                                             )).select_by_value(locale)
                if edit:
                    self._configure_user(roles=roles, locations=locations,
                                         organizations=organizations,
                                         select=select)
                self.wait_until_element(common_locators["submit"]).click()
                self.wait_for_ajax()
        else:
            raise Exception(
                "Unable to create the User '%s'" % username)

    def search(self, name, search_key):
        """
        Searches existing user from UI
        """
        nav = Navigator(self.browser)
        nav.go_to_users()
        element = self.search_entity(name, locators["users.user"],
                                     search_key=search_key)
        return element

    def delete(self, name, search_key, really=False):
        """
        Deletes existing user from UI.
        """
        self.delete_entity(name, really, locators["users.user"],
                           locators["users.delete"], search_key=search_key)

    def update(self, search_key, username, new_username=None,
               email=None, password=None,
               first_name=None, last_name=None, locale=None,
               roles=None, new_roles=None, locations=None,
               new_locations=None, organizations=None,
               new_organizations=None, select=False):
        """
        Update username, email, password, firstname,
        lastname and locale from UI
        """

        element = self.search(username, search_key)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_username:
                self.field_update("users.username", new_username)
            if email:
                self.field_update("users.email", email)
            if first_name:
                self.field_update("users.firstname", first_name)
            if last_name:
                self.field_update("users.lastname", last_name)
            if locale:
                Select(self.find_element(locators["users.language"]
                                         )).select_by_value(locale)
            if password:
                self.field_update("users.password", password)
                self.field_update("users.password_confirmation", password)
            self._configure_user(roles=roles, new_roles=new_roles,
                                 locations=locations,
                                 new_locations=new_locations,
                                 organizations=organizations,
                                 new_organizations=new_organizations,
                                 select=select)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception("Unable to find the username '%s' for update."
                            % username)
