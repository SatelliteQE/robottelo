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

            self.wait(2) #it takes few seconds for the org selector to populate
            if self.find_element(locators["login.interstitial"]):
                self.find_element((locators["login.selectOrg"][0],locators["login.selectOrg"][1] % organization)).click()

    def logout(self):
        # Headpin ?
        if self.find_element(locators["login.gravatar"]):
            self.find_element(locators["login.gravatar"]).click()
        # Katello ?
        elif self.find_element(locators["login.user"]):
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

    def forgot_username(self, email):

        email = email or "test@test.com"
        if self.wait_until_element(locators["login.forgotUserName"]):
            self.find_element(locators["login.forgotUserName"]).click()
            if self.wait_until_element(locators["login.forgotUserNameEmail"]):
                txt_field = self.find_element(locators["login.forgotUserNameEmail"])
                txt_field.clear()
                txt_field.send_keys(email)
                if self.wait_until_element(locators["login.forgotUserNameSubmit"]):
                    self.find_element(locators["login.forgotUserNameSubmit"]).click()


    def check_usermessage(self, criteria):
        if criteria == "success":
            if self.wait_until_element(locators["notif.success"]):
                return True
            else:
                return False
        elif criteria == "error":
            if self.wait_until_element(locators["notif.error"]):
                return True
        else:
            return False





