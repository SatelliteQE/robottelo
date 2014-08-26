# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Login UI
"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class Login(Base):
    """
    Implements login, logout functions for Foreman UI
    """

    def login(self, username, password, organization=None, location=None):
        """
        Logins user from UI
        """

        if self.wait_until_element(locators["login.username"]):
            self.field_update("login.username", username)
            self.field_update("login.password", password)

            self.find_element(common_locators["submit"]).click()

            if self.find_element(common_locators["notif.error"]):
                return
            if location:
                nav = Navigator(self.browser)
                nav.go_to_select_loc(location)
            if organization:
                nav = Navigator(self.browser)
                nav.go_to_select_org(organization)

    def logout(self):
        """
        Logout user from UI
        """

        if self.find_element(locators["login.gravatar"]) is None:
            raise UINoSuchElementError(
                "could not find login.gravatar to sign out")
        nav = Navigator(self.browser)
        nav.go_to_sign_out()
        self.wait_for_ajax()

    def is_logged(self):
        """
        Checks whether an user is logged
        """

        if self.find_element(locators["login.gravatar"]):
            return True
        else:
            return False
