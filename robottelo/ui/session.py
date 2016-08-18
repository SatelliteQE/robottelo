# -*- encoding: utf-8 -*-

from robottelo.config import settings
from robottelo.ui.login import Login
from robottelo.ui.navigator import Navigator


class Session(object):
    """A session context manager that manages login and logout"""

    def __init__(self, browser, user=None, password=None):
        self._login = Login(browser)
        self.browser = browser
        self.nav = Navigator(browser)
        self.password = password
        self.user = user

        if self.user is None:
            self.user = getattr(
                self.browser, 'foreman_user', settings.server.admin_username
            )

        if self.password is None:
            self.password = getattr(
                self.browser,
                'foreman_password',
                settings.server.admin_password
            )

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.logout()

    def login(self):
        """Utility function to call Login instance login method"""
        self._login.login(self.user, self.password)

    def logout(self):
        """Utility function to call Login instance logout method"""
        self._login.logout()

    def close(self):
        """Exits session and also closes the browser (used in shell)"""
        self.browser.close()
