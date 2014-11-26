"""Test class for Subscriptions/Manifests UI"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo import entities
from robottelo.common import manifests
from robottelo.common.decorators import skipRemote
from robottelo.common.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@ddt
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def setUpClass(cls):
        cls.org_name = entities.Organization().create()['name']

        super(SubscriptionTestCase, cls).setUpClass()

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_positive_upload_1(self):
        """@Test: Upload a manifest with minimal input parameters

        @Feature: Manifest/Subscription - Positive Create

        @Assert: Manifest is uploaded

        """

        alert_loc = common_locators['alert.success']
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            success_ele = self.subscriptions.wait_until_element(alert_loc)
            self.assertTrue(success_ele)

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_positive_delete_1(self):
        """@Test: Upload a manifest and delete the manifest.

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is Deleted successfully

        """

        alert_loc = common_locators['alert.success']
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            self.subscriptions.delete()
            success_ele = self.subscriptions.wait_until_element(alert_loc)
            self.assertTrue(success_ele)

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_assert_delete_button(self):
        """@Test: Upload and delete a manifest

        @Feature: Manifest/Subscription - Positive Delete

        @Assert: Manifest is Deleted. Delete button is asserted . Subscriptions
        is asserted

        """
        alert_loc = common_locators['alert.success']
        del_mf = locators['subs.delete_manifest']
        manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(manifest_path, remote_file=manifest_path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(manifest_path)
            self.subscriptions.delete()
            self.assertTrue(self.subscriptions.wait_until_element(alert_loc))
            self.assertTrue(self.subscriptions.wait_until_element(del_mf))
            self.assertIsNone(
                self.subscriptions.search("Red Hat Employee Subscription"))
