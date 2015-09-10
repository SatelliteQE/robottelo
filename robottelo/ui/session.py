# -*- encoding: utf-8 -*-

from robottelo.config import conf
from robottelo.ui.login import Login
from robottelo.ui.navigator import Navigator


class Session(object):
    """A session context manager that manages login and logout"""

    def __init__(self, browser, user=None, password=None):
        self.browser = browser
        self._login = Login(browser)
        self.nav = Navigator(browser)

        if user is None:
            self.user = conf.properties['foreman.admin.username']
        else:
            self.user = user

        if password is None:
            self.password = conf.properties['foreman.admin.password']
        else:
            self.password = password

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.logout()

    def login(self):
        """Utility funtion to call Login instance login method"""
        self._login.login(self.user, self.password)

    def logout(self):
        """Utility function to call Login instance logout method"""
        self._login.logout()
