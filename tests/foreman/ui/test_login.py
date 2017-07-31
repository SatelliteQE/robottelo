# -*- encoding: utf-8 -*-
"""Test class for Login UI

:Requirement: Login

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import tier1
from robottelo.test import UITestCase
from robottelo.ui.session import Session


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
    """Implements the login tests from UI"""

    @tier1
    def test_positive_login(self):
        """Login as an admin user

        :id: 7ec027ec-4c51-460a-81f9-643e5bb2c5f5

        :expectedresults: Successfully logged in as an admin user

        :CaseImportance: Critical
        """
        with Session(
                self, user=self.foreman_user, password=self.foreman_password):
            self.assertTrue(self.login.is_logged())

    @tier1
    def test_negative_login(self):
        """Login into application using invalid credentials

        :id: 23090dce-b918-4a8e-8481-188ea76c376d

        :expectedresults: Fails to login

        :CaseImportance: Critical
        """
        for test_data in invalid_credentials():
            with self.subTest(test_data):
                with Session(
                    self, test_data['login'], password=test_data['pass']
                ) as session:
                    self.assertFalse(session.login.is_logged())
