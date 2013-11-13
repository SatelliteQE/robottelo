#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators
from selenium.webdriver.common.keys import Keys


class User(Base):

    def __init__(self, browser):
        self.browser = browser

    def new_user(self, username, email=None, password1=None, password2=None):
        self.wait_until_element(locators["users.new"]).click()

        if self.wait_until_element(locators["users.username"]):
            self.find_element(locators["users.username"]).send_keys(username)
            # The following fields are not available via LDAP auth
            if self.wait_until_element(locators["users.email"]):
                self.find_element(locators["users.email"]).send_keys(email)
            if self.wait_until_element(locators["users.password1"]):
                self.find_element(locators["users.password1"]).send_keys(password1)
            if self.wait_until_element(locators["users.password2"]):
                self.find_element(locators["users.password2"]).send_keys(password2)
            self.find_element(locators["users.save"]).click()

    def find_user(self, username):
        # Make sure the user is present

        user = None

        searchbox = self.wait_until_element(locators["users.search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(username)
            searchbox.send_keys(Keys.RETURN)
            user = self.wait_until_element((locators["users.user"][0], locators["users.user"][1] % username))
            if user:
                user.click()

        return user

    def remove_user(self, username, really=False):
        element = self.wait_until_element(locators["users.remove"])
        if element:
            self.find_element(locators["users.remove"]).click()
            if really:
                self.find_element(locators["dialog.yes"]).click()
            else:
                self.find_element(locators["dialog.no"]).click()

    def update_locale(self, lang='pt-BR'):

        self.wait_until_element(locators["users.locale"])
        select = self.browser.find_element_by_tag_name("select")
        allOptions = select.find_elements_by_tag_name("option")
        for option in allOptions:
            if option.get_attribute("value") == lang:
                option.click()
                break

