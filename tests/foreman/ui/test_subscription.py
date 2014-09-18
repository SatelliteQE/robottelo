"""Test class for Subscriptions/Manifests UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.common.decorators import skipRemote
from robottelo.common.manifests import clone
from robottelo.common.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    org_name = None

    def setUp(self):
        super(SubscriptionTestCase, self).setUp()
        # Make sure to use the Class' org_name instance
        if SubscriptionTestCase.org_name is None:
            SubscriptionTestCase.org_name = FauxFactory.generate_string(
                "alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=SubscriptionTestCase.org_name)

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_positive_upload_1(self):
        """@Test: Upload a manifest with minimal input parameters

        @Feature: Manifest/Subscription - Positive Create

        @Assert: Manifest is uploaded

        """

        alert_loc = common_locators['alert.success']
        path = clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(path, remote_file=path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(path)
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
        path = clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(path, remote_file=path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(path)
            self.subscriptions.delete()
            success_ele = self.subscriptions.wait_until_element(alert_loc)
            self.assertTrue(success_ele)
