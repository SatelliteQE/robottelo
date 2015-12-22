"""Test class for Subscriptions/Manifests UI"""
from nailgun import entities
from robottelo import manifests
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.decorators import skip_if_not_set, tier1
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(SubscriptionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_upload_basic(self):
        """@Test: Upload a manifest with minimal input parameters

        @Feature: Manifest/Subscription - Positive Create

        @Assert: Manifest is uploaded successfully
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_delete(self):
        """@Test: Upload a manifest and then delete it

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is deleted successfully
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_assert_delete_button(self):
        """@Test: Upload and delete a manifest

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is Deleted. Delete button is asserted. Subscriptions
        is asserted
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))
            self.assertTrue(self.subscriptions.wait_until_element(
                locators['subs.delete_manifest']))
            self.assertIsNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
