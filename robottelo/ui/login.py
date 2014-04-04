# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Login UI
"""

from robottelo.common.helpers import generate_name
from robottelo.ui.base import Base
from robottelo.ui.location import Location
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class Login(Base):
    """
    Implements login, logout functions for Foreman UI
    """

    def login(self, username, password, organization=None):
        """
        Logins user from UI
        """

        if self.wait_until_element(locators["login.username"]):
            self.field_update("login.username", username)
            self.field_update("login.password", password)

            self.find_element(common_locators["submit"]).click()

            if self.find_element(common_locators["notif.error"]):
                return
            if self.find_element(locators["location.new"]):
                loc = Location(self.browser)
                loc.create(generate_name())
            if organization:
                nav = Navigator(self.browser)
                nav.go_to_select_org(organization)

    def logout(self):
        """
        Logout user from UI
        """

        if self.find_element(locators["login.gravatar"]):
            nav = Navigator(self.browser)
            nav.go_to_sign_out()
        else:
            raise Exception(
                "could not find login.gravatar to sign out")

    def is_logged(self):
        """
        Checks whether an user is logged
        """

        if self.find_element(locators["login.gravatar"]):
            return True
        else:
            return False
