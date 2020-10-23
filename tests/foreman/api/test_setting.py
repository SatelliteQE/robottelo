# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values

:Requirement: Settings

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Settings

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.cleanup import setting_cleanup
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class SettingTestCase(APITestCase):
    """Implements tests for Settings for API"""

    @run_in_one_thread
    @tier1
    @upgrade
    def test_positive_update_login_page_footer_text(self):
        """Updates parameter "login_text" in settings

        :id: 91c5373d-b928-419d-8509-761adf5b94b0

        :CaseImportance: Critical

        :expectedresults: Parameter is updated successfully
        """
        login_text_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="login_text"'}
            )
        ][0]
        login = entities.Setting(id=login_text_id).read()
        for login_text in valid_data_list():
            with self.subTest(login_text):
                login.value = login_text
                login = login.update(['value'])
                self.assertEqual(login.value, login_text)

    @run_in_one_thread
    @tier2
    def test_positive_update_login_page_footer_text_without_value(self):
        """Updates parameter "login_text" without any string (empty value)

        :id: 7a56f194-8bde-4dbf-9993-62eb6ab10733

        :expectedresults: login_text has empty value after update
        """
        login_text_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="login_text"'}
            )
        ][0]
        login = entities.Setting(id=login_text_id).read()
        login.value = ""
        login = login.update(['value'])
        self.assertEqual(login.value, "")

    @run_in_one_thread
    @tier2
    def test_positive_update_login_page_footer_text_with_long_string(self):
        """Attempt to update parameter "Login_page_footer_text"
            with long length string

        :id: fb8b0bf1-b475-435a-926b-861aa18d31f1

        :expectedresults: Parameter is updated
        """
        login_text_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="login_text"'}
            )
        ][0]
        login = entities.Setting(id=login_text_id).read()
        for login_text in generate_strings_list(1000):
            with self.subTest(login_text):
                login.value = login_text
                login = login.update(['value'])
                self.assertEqual(login.value, login_text)

    @pytest.mark.skip_if_open("BZ:1470083")
    @tier2
    def test_negative_update_hostname_with_empty_fact(self):
        """Update the Hostname_facts settings without any string(empty values)

        :id: b8e260fc-e263-4292-aa2f-ab37085c7758

        :expectedresults: Error should be raised on setting empty value for
            hostname_facts setting
        """
        hostname_facts_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="discovery_hostname"'}
            )
        ][0]
        facts = entities.Setting(id=hostname_facts_id).read()
        original_value = facts.value
        facts.value = ""
        try:
            facts = facts.update(['value'])
            self.assertNotEqual(facts.value, "", msg="Empty string")
        finally:
            setting_cleanup("discovery_hostname", original_value)

    @tier2
    def test_positive_update_hostname_prefix_without_value(self):
        """Update the Hostname_prefix settings without any string(empty values)

        :id: 3867488c-d955-47af-ac0d-71f4016391d1

        :expectedresults: Hostname_prefix should be set without any text
        """
        hostname_prefix_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="discovery_prefix"'}
            )
        ][0]
        prefix = entities.Setting(id=hostname_prefix_id).read()
        original_value = prefix.value
        prefix.value = ""
        try:
            prefix = prefix.update(['value'])
            self.assertEqual(prefix.value, "")
        finally:
            setting_cleanup("discovery_prefix", original_value)

    @tier1
    def test_positive_update_hostname_default_prefix(self):
        """Update the default set prefix of hostname_prefix setting

        :id: 4969994d-f934-4f0e-9a98-476b87eb0527

        :CaseImportance: Critical

        :expectedresults: Default set prefix should be updated with new value
        """
        hostname_prefix_id = [
            ele.id
            for ele in entities.Setting().search(
                query={"per_page": 200, 'search': 'name="discovery_prefix"'}
            )
        ][0]
        prefix = entities.Setting(id=hostname_prefix_id).read()
        original_value = prefix.value
        try:
            for discovery_prefix in generate_strings_list(
                exclude_types=['alphanumeric', 'numeric']
            ):
                prefix.value = discovery_prefix
                prefix = prefix.update(['value'])
                self.assertEqual(prefix.value, discovery_prefix)
        finally:
            setting_cleanup("discovery_prefix", original_value)

    @pytest.mark.stubbed
    @tier2
    def test_positive_update_hostname_default_facts(self):
        """Update the default set fact of hostname_facts setting with list of
        facts like: bios_vendor,uuid

        :id: aa60d383-d193-4983-a8d7-3994e60a064b

        :expectedresults: Default set fact should be updated with facts list.

        :CaseAutomation: notautomated
        """

    @pytest.mark.stubbed
    @tier2
    def test_negative_discover_host_with_invalid_prefix(self):
        """Update the hostname_prefix with invalid string like
        -mac, 1mac or ^%$

        :id: 51091ed2-b0a2-433c-bcef-c8b4a3a34a05

        :expectedresults: Validation error should be raised on updating
            hostname_prefix with invalid string, should start w/ letter

        :CaseAutomation: notautomated
        """

    @run_in_one_thread
    @tier2
    def test_positive_custom_repo_download_policy(self):
        """ Check the set custom repository download policy for newly created custom repository.

        :id: d5150cce-ba85-4ea0-a8d1-6a54d0d29571

        :Steps:
            1. Create a product, Organization
            2. Update the Default Custom Repository download policy in the setting.
            3. Create a custom repo under the created organization.
            4. Check the set policy of new created repository.
            5. Repeat steps 2 to 4 for both download policy.

        :expectedresults: The set download policy should be the default policy in the newly created
         repository.

        :CaseImportance: Medium

        :CaseLevel: Acceptance
        """
        download_policy_id = "default_download_policy"
        download_policies = ["immediate", "on_demand"]
        download_policy_property = entities.Setting().search(
            query={'search': f'name={download_policy_id}'}
        )[0]
        default_property_value = download_policy_property.value
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        try:
            for download_policy in download_policies:
                download_policy_property.value = download_policy
                download_policy_property.update({'value'})
                repo = entities.Repository(
                    product=prod, content_type='yum', organization=org
                ).create()
                assert repo.download_policy == download_policy
                repo.delete()
        finally:
            prod.delete()
            setting_cleanup(setting_name=download_policy_id, setting_value=default_property_value)
