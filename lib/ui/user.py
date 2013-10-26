#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import *

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

        user = self.wait_until_element((locators["users.user"][0], locators["users.user"][1] % username))
        if not user:
            print "No users were found."

        return user

    def remove_user(self, username, really=False):
        user = self.find_user(username)

        if user:
            user.click()
            #TODO: Need to wait until the edit panel is visible so we
            #can interact with it.
            element = self.find_and_wait(self.browser.find_by_xpath, locators["users.remove"])
            if element:
                self.browser.find_by_xpath(locators["users.remove"]).click()
                if really:
                    self.browser.find_by_xpath(locators["dialog.yes"]).click()
                else:
                    self.browser.find_by_xpath(locators["dialog.no"]).click()

    def update_locale(self, lang='pt-BR'):
        self.browser.select(locators["users.locale"], lang)

