"""Test class for Subscriptions/Manifests UI"""

from ddt import ddt
from nailgun import entities
from robottelo import manifests
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.decorators import skipRemote
from robottelo.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@ddt
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        cls.organization = entities.Organization().create()

        super(SubscriptionTestCase, cls).setUpClass()

    @skipRemote
    def test_positive_upload_basic(self):
        """@Test: Upload a manifest with minimal input parameters

        @Feature: Manifest/Subscription - Positive Create

        @Assert: Manifest is uploaded

        """
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))

    @skipRemote
    def test_positive_delete(self):
        """@Test: Upload a manifest and then delete it

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is deleted successfully

        """
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))

    @skipRemote
    def test_assert_delete_button(self):
        """@Test: Upload and delete a manifest

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is Deleted. Delete button is asserted. Subscriptions
        is asserted

        """
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(
                common_locators['alert.success']))
            self.assertTrue(self.subscriptions.wait_until_element(
                locators['subs.delete_manifest']))
            self.assertIsNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
