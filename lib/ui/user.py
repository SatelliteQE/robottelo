#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class User(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, username, email=None, password1=None, password2=None, authorized_by="INTERNAL", locale=None):
        self.wait_until_element(locators["users.new"]).click()

        if self.wait_until_element(locators["users.username"]):
            self.find_element(locators["users.username"]).send_keys(username)
            Select(self.find_element(locators["users.authorized_by"])).select_by_visible_text(authorized_by)
            # The following fields are not available via LDAP auth
            if self.wait_until_element(locators["users.email"]):
                self.find_element(locators["users.email"]).send_keys(email)
            if self.wait_until_element(locators["users.password"]):
                self.find_element(locators["users.password"]).send_keys(password1)
            if self.wait_until_element(locators["users.password_confirmation"]):
                self.find_element(locators["users.password_confirmation"]).send_keys(password2)
            if locale:
                Select(self.find_element(locators["users.language"])).select_by_value(locale)
            self.find_element(locators["submit"]).click()

    def search(self, username):
        # Make sure the user is present

        user = None

        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(username)
            searchbox.send_keys(Keys.RETURN)
            user = self.wait_until_element((locators["users.user"][0], locators["users.user"][1] % username))
        return user

    def delete(self, username, really=False):
        self.search(username)
        element = self.wait_until_element((locators["users.delete"][0], locators["users.delete"][1] % username))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)

    def update(self, username, new_username=None, email=None, password=None, firstname=None, lastname=None, locale=None):
        element = self.search(username)
        if element:
            element.click()
            self.wait_for_ajax()
            if new_username:
                self.field_update("users.username", new_username)
            if email:
                self.field_update("users.email", email)
            if firstname:
                self.field_update("users.firstname", firstname)
            if lastname:
                self.field_update("users.lastname", lastname)
            if locale:
                Select(self.find_element(locators["users.language"])).select_by_value(locale)
            if password:
                self.field_update("users.password", password)
                self.field_update("users.password_confirmation", password)
            self.find_element(locators["submit"]).click()
