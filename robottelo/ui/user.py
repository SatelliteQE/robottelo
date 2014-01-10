# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements User UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class User(Base):
    """
    Implements CRUD functions from UI
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, username, email=None, password1=None,
               password2=None, authorized_by="INTERNAL", locale=None):
        """
        Create new user from UI
        """

        self.wait_until_element(locators["users.new"]).click()

        if self.wait_until_element(locators["users.username"]):
            self.find_element(locators["users.username"]).send_keys(username)
            Select(self.find_element(locators["users.authorized_by"]
                                     )).select_by_visible_text(authorized_by)
            # The following fields are not available via LDAP auth
            if self.wait_until_element(locators["users.email"]):
                self.find_element(locators["users.email"]).send_keys(email)
            if self.wait_until_element(locators["users.password"]):
                self.find_element(locators
                                  ["users.password"]).send_keys(password1)
            if self.wait_until_element(locators
                                       ["users.password_confirmation"]):
                self.find_element(locators["users.password_confirmation"]
                                  ).send_keys(password2)
            if locale:
                Select(self.find_element(locators["users.language"]
                                         )).select_by_value(locale)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def delete(self, username, search_key, really=False):
        """
        Delete existing user from UI
        """

        element = self.search(username, locators['users.delete'], search_key)

        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)
        else:
            raise Exception(
                "Could not delete the user '%s'" % username)

    def update(self, search_key, username, new_username=None,
               email=None, password=None,
               first_name=None, last_name=None, locale=None,
               role=None):
        """
        Update username, email, password, firstname,
        lastname and locale from UI
        """

        element = self.search(username, locators['users.user'], search_key)

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
            if role:
                self.select_entity("users.role",
                                   "users.select_role", role,
                                   "users.tab_roles")
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
