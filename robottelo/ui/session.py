# -*- encoding: utf-8 -*-
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.ui.factory import make_org
from robottelo.ui.login import Login
from robottelo.ui.navigator import Navigator

_org_cache = {}


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

    def get_org_name(self):
        """
        Make a Organization and cache its name to be returned through session,
        avoiding overhead of its recreation on each test.

        Organization Must be at same state (not mutate) at the end of the test

        Create your own organization if mutation is needed. Otherwise other
        tests can break with your tests side effects

        :return: str: Organization name
        """
        if 'org_name' in _org_cache:
            return _org_cache['org_name']
        org_name = gen_string('alpha')
        make_org(self, org_name=org_name)
        _org_cache['org_name'] = org_name
        return org_name
