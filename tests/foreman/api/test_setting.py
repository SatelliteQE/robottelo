# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1
from robottelo.test import APITestCase


class SettingTestCase(APITestCase):
    """Implements tests for Settings for API"""

    @stubbed
    @tier1
    def test_positive_update_login_page_footer_text(self):
        """Updates parameter "login_text" in settings

        :id: 91c5373d-b928-419d-8509-761adf5b94b0

        :expectedresults: Parameter is updated successfully

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_login_page_footer_text_without_value(self):
        """Updates parameter "login_text" without any string (empty value)

        :id: 7a56f194-8bde-4dbf-9993-62eb6ab10733

        :expectedresults: login_text has empty value after update

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_login_page_footer_text(self):
        """Attempt to update parameter "Login_page_footer_text"
            with invalid value(long length)

        :id: fb8b0bf1-b475-435a-926b-861aa18d31f1

        :expectedresults: Parameter is not updated

        :caseautomation: notautomated
        """
