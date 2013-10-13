#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from locators import *

class User():

    def __init__(self, browser):
        self.browser = browser

    def new_user(self, username, email=None, password1=None, password2=None):
        self.browser.find_by_id(locators["users.new"]).click()

        if self.browser.is_element_present_by_id(locators["users.username"], 10):
            self.browser.find_by_id(locators["users.username"]).fill(username)
            # The following fields are not available via LDAP auth
            if self.browser.is_element_present_by_id(locators["users.email"], 10):
                self.browser.find_by_id(locators["users.email"]).fill(email)
            if self.browser.is_element_present_by_id(locators["users.password1"], 10):
                self.browser.find_by_id(locators["users.password1"]).fill(password1)
            if self.browser.is_element_present_by_id(locators["users.password2"], 10):
                self.browser.find_by_id(locators["users.password2"]).fill(password2)
            self.browser.find_by_id(locators["users.save"]).click()

    def find_user(self, username):
        return self.browser.find_by_xpath(locators["users.user"] % username, 10)

    def remove_user(self, username, really=False):
        user = self.find_user(username)

        if user:
            user.click()
            #TODO: Need to wait until the edit panel is visible so we
            #can interact with it.
            if self.browser.is_element_present_by_xpath(locators["users.remove"], 10):
                self.browser.find_by_xpath(locators["users.remove"]).click()
                if really:
                    self.browser.find_by_xpath(locators["dialog.yes"]).click()
                else:
                    self.browser.find_by_xpath(locators["dialog.no"]).click()

    def update_locale(self, lang='pt-BR'):
        self.browser.select(locators["users.locale"], lang)

