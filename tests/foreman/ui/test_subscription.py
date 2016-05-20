"""Test class for Subscriptions/Manifests UI"""
from nailgun import entities
from robottelo import manifests
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.decorators import skip_if_not_set, tier1
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(SubscriptionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_upload_and_delete(self):
        """Upload a manifest with minimal input parameters and delete it

        @Feature: Manifest/Subscription

        @Assert: Manifest is uploaded and deleted successfully
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            # Step 1: Attempt to upload a manifest
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))
            # Step 2: Attempt to delete the manifest
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))
            self.assertIsNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
