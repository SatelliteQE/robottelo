# -*- encoding: utf-8 -*-
"""Test class for Login UI

@Requirement: Login

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import tier1
from robottelo.test import UITestCase


@filtered_datapoint
def invalid_credentials():
    """Returns a list of invalid credentials"""
    return [
        {u'login': 'admin', u'pass': ''},
        {u'login': '', u'pass': 'mypassword'},
        {u'login': '', u'pass': ''},
        {u'login': gen_string('alpha', 300), u'pass': ''},
        {u'login': gen_string('alpha', 300),
         u'pass': gen_string('alpha', 300)},
    ]


class LoginTestCase(UITestCase):
    """Implements the login tests rom UI"""

    @tier1
    def test_positive_login(self):
        """Login as an admin user

        @id: 7ec027ec-4c51-460a-81f9-643e5bb2c5f5

        @Assert: Successfully logged in as an admin user
        """
        self.login.login(self.foreman_user,
                         self.foreman_password)
        self.assertTrue(self.login.is_logged())

    @tier1
    def test_negative_login(self):
        """Login into application using invalid credentials

        @id: 23090dce-b918-4a8e-8481-188ea76c376d

        @Assert: Fails to login
        """
        for test_data in invalid_credentials():
            with self.subTest(test_data):
                self.login.login(test_data['login'], test_data['pass'])
                self.assertFalse(self.login.is_logged())
