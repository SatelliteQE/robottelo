# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Login UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Login(Base):
    """
    Implements login, logout functions for Foreman UI
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def login(self, username, password, organization=None):
        """
        Logins user from UI
        """

        organization = organization or 'ACME_Corporation'

        if self.wait_until_element(locators["login.username"]):
            self.field_update("login.username", username)
            self.field_update("login.password", password)

            self.find_element(locators["login.submit"]).click()

            if self.find_element(locators["notif.error"]):
                return

    def logout(self):
        """
        Logout user from UI
        """

        if self.find_element(locators["login.gravatar"]):
            nav = Navigator(self.browser)
            nav.go_to_sign_out()

    def is_logged(self):
        """
        Checks whether an user is logged
        """

        if self.find_element(locators["login.gravatar"]):
            return True
        else:
            return False
