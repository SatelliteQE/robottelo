# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment UI
"""

import unittest

from tests.ui.baseui import BaseUI
from robottelo.ui.locators import common_locators
from robottelo.common.helpers import generate_name


class Environment(BaseUI):

    def test_create_env(self):
        "create new Environment"
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_environments()
        self.environment.create(name)
        # TODO: assertion is pending Foreman issue #3826
        #search = self.environment.search(name, locators["env.env_name"])
        #self.assertIsNotNone(search)

    @unittest.skip("http://projects.theforeman.org/issues/3826")
    def test_remove_env(self):
        "Delete an Environment "
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_environments()
        self.environment.create(name)
        self.environment.delete(name, really=True)
        notif = self.user.wait_until_element(common_locators["notif.success"])
        self.assertTrue(notif)
