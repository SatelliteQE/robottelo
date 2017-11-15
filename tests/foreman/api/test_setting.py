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
from nailgun import entities
from robottelo.datafactory import generate_strings_list, valid_data_list
from robottelo.decorators import run_in_one_thread, tier1, upgrade
from robottelo.test import APITestCase


class SettingTestCase(APITestCase):
    """Implements tests for Settings for API"""

    @run_in_one_thread
    @tier1
    @upgrade
    def test_positive_update_login_page_footer_text(self):
        """Updates parameter "login_text" in settings

        :id: 91c5373d-b928-419d-8509-761adf5b94b0

        :expectedresults: Parameter is updated successfully
        """
        login_text_id = [ele.id for ele in entities.Setting().search(query={
            "per_page": 200,
            'search': 'name="login_text"'
        })][0]
        login = entities.Setting(id=login_text_id).read()
        for login_text in valid_data_list():
            with self.subTest(login_text):
                login.value = login_text
                login = login.update(['value'])
                self.assertEqual(login.value, login_text)

    @run_in_one_thread
    @tier1
    def test_positive_update_login_page_footer_text_without_value(self):
        """Updates parameter "login_text" without any string (empty value)

        :id: 7a56f194-8bde-4dbf-9993-62eb6ab10733

        :expectedresults: login_text has empty value after update
        """
        login_text_id = [ele.id for ele in entities.Setting().search(query={
            "per_page": 200,
            'search': 'name="login_text"'
        })][0]
        login = entities.Setting(id=login_text_id).read()
        login.value = ""
        login = login.update(['value'])
        self.assertEqual(login.value, "")

    @run_in_one_thread
    @tier1
    def test_positive_update_login_page_footer_text_with_long_string(self):
        """Attempt to update parameter "Login_page_footer_text"
            with long length string

        :id: fb8b0bf1-b475-435a-926b-861aa18d31f1

        :expectedresults: Parameter is updated
        """
        login_text_id = [ele.id for ele in entities.Setting().search(query={
            "per_page": 200,
            'search': 'name="login_text"'
        })][0]
        login = entities.Setting(id=login_text_id).read()
        for login_text in generate_strings_list(1000):
            with self.subTest(login_text):
                login.value = login_text
                login = login.update(['value'])
                self.assertEqual(login.value, login_text)
