# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Login UI
"""
import unittest

from robottelo.ui.base import Base
from robottelo.common.constants import DEFAULT_ORG
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator
from robottelo.ui.org import Org


class Login(Base, unittest.TestCase):
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

        organization = organization or DEFAULT_ORG

        if self.wait_until_element(locators["login.username"]):
            self.field_update("login.username", username)
            self.field_update("login.password", password)

            self.find_element(common_locators["submit"]).click()

            if self.find_element(common_locators["notif.error"]):
                return
            if organization:
                nav = Navigator(self.browser)
                try:
                    nav.go_to_select_org(organization)
                except Exception:
                    org_inst = Org(self.browser)
                    nav.go_to_org()
                    org_inst.create(organization)
                    nav.go_to_org()
                    nav.go_to_select_org(organization)

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
