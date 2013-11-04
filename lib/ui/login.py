#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import *

class Login(Base):

    def __init__(self, browser):
        self.browser = browser

    def login(self, username, password, organization=None):

        organization = organization or 'ACME_Corporation'

        if self.wait_until_element(locators["login.username"]):
            txt_field = self.find_element(locators["login.username"])
            txt_field.clear()
            txt_field.send_keys(username)
            txt_field = self.find_element(locators["login.password"])
            txt_field.clear()
            txt_field.send_keys(password)

            self.find_element(locators["login.submit"]).click()

            if self.find_element(locators["notif.error"]):
                return

            if self.find_element(locators["login.interstitial"]):
                self.find_element((locators["login.selectOrg"][0],locators["login.selectOrg"][1] % organization)).click()

    def logout(self):

        if self.find_element(locators["login.user"]):
            self.find_element(locators["login.user"]).click()
            self.find_element(locators["login.logout"]).click()

    def is_logged(self, username):
        # Headpin?
        if self.find_element(locators["login.gravatar"]):
            return True
        # Katello?
        elif self.find_element(locators["login.user"]):
            return True
        else:
            return False
