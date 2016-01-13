# -*- encoding: utf-8 -*-
"""Implements Login UI"""

import requests

from robottelo.config import settings
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Login(Base):
    """Implements login, logout functions for Foreman UI"""

    def login(self, username, password, organization=None, location=None):
        """Logins user from UI"""
        if self.wait_until_element(locators['login.username']):
            self.field_update('login.username', username)
            self.field_update('login.password', password)

            self.click(common_locators['submit'])

            if self.find_element(common_locators['notif.error']):
                return
            if location:
                nav = Navigator(self.browser)
                nav.go_to_select_loc(location)
            if organization:
                nav = Navigator(self.browser)
                nav.go_to_select_org(organization)

    def logout(self):
        """Logout user from UI"""
        # Scroll to top
        self.browser.execute_script('window.scroll(0, 0)')
        if self.wait_until_element(locators['login.gravatar']) is None:
            raise UINoSuchElementError(
                'could not find login.gravatar to sign out')
        Navigator(self.browser).go_to_sign_out()

    def is_logged(self):
        """Checks whether user is logged by validating a session cookie"""
        cookies = dict(
            (cookie['name'], cookie['value'])
            for cookie in self.browser.get_cookies()
        )
        # construct the link to the Dashboard web page
        url_root = settings.server.get_url() + '/dashboard'

        response = requests.get(
            url_root,
            verify=False,
            allow_redirects=False,
            cookies=cookies
        )
        response.raise_for_status()
        return (
            response.status_code != 302 or
            not response.headers['location'].endswith('/login')
        )
