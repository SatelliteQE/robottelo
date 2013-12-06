#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.ui.base import Base
from lib.ui.locators import locators
from lib.ui.navigator import Navigator


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

    def logout(self):
        if self.find_element(locators["login.gravatar"]):
            nav = Navigator(self.browser)
            nav.go_to_sign_out()

    def is_logged(self):
        if self.find_element(locators["login.gravatar"]):
            return True
        else:
            return False
