"""Test class for Subscriptions/Manifests UI

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo import manifests
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.decorators import run_in_one_thread, skip_if_not_set, tier1
from robottelo.test import UITestCase
from robottelo.ui.locators import locators
from robottelo.ui.session import Session


@run_in_one_thread
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def set_session_org(cls):
        cls.session_org = entities.Organization().create()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_upload_and_delete(self):
        """Upload a manifest with minimal input parameters and delete it

        :id: 58e549b0-1ba3-421d-8075-dcf65d07510b

        :expectedresults: Manifest is uploaded and deleted successfully

        :CaseImportance: Critical
        """
        with Session(self.browser):
            # Step 1: Attempt to upload a manifest
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(self.subscriptions.wait_until_element_exists(
                locators['subs.import_history.imported']))
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
            # Step 2: Attempt to delete the manifest
            self.subscriptions.delete()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_negative_delete(self):
        """Upload a manifest with minimal input parameters and attempt to
        delete it but hit 'Cancel' button on confirmation screen

        :id: dbb68a99-2935-4124-8927-e6385e7eecd6

        :BZ: 1266827

        :expectedresults: Manifest was not deleted

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(self.subscriptions.wait_until_element_exists(
                locators['subs.import_history.imported']))
            self.subscriptions.delete(really=False)
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
