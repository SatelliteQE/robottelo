"""
Test class for Subscriptions/Manifests UI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.decorators import skipRemote
from robottelo.common.helpers import generate_string
from robottelo.common.manifests import manifest
from robottelo.common.ssh import upload_file
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from tests.foreman.ui.baseui import BaseUI


@ddt
class Subscription(BaseUI):
    """
    Implements subscriptions/manifests tests in UI
    """

    org_name = None

    def setUp(self):
        super(Subscription, self).setUp()
        # Make sure to use the Class' org_name instance
        if Subscription.org_name is None:
            Subscription.org_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Subscription.org_name)

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_positive_upload_1(self):
        """
        @Feature: Manifest/Subscription - Positive Create
        @Test: Upload a manifest with minimal input parameters
        @Assert: Manifest is uploaded
        """

        alert_loc = common_locators['alert.success']
        mdetails = manifest.fetch_manifest()
        path = mdetails['path']
        try:
            # upload_file function should take care of uploading to sauce labs.
            upload_file(mdetails['path'], remote_file=mdetails['path'])
            with Session(self.browser) as session:
                session.nav.go_to_select_org(self.org_name)
                session.nav.go_to_red_hat_subscriptions()
                self.subscriptions.upload(path)
                success_ele = self.subscriptions.wait_until_element(alert_loc)
                self.assertTrue(success_ele)
        finally:
            manifest.delete_distributor(ds_uuid=mdetails['uuid'])

    @skipRemote
    @attr('ui', 'subs', 'implemented')
    def test_positive_delete_1(self):
        """
        @Feature: Manifest/Subscription - Positive Delete
        @Test: Upload a manifest and delete the manifest.
        @Assert: Manifest is Deleted successfully
        """

        alert_loc = common_locators['alert.success']
        mdetails = manifest.fetch_manifest()
        path = mdetails['path']
        try:
            # upload_file function should take care of uploading to sauce labs.
            upload_file(mdetails['path'], remote_file=mdetails['path'])
            with Session(self.browser) as session:
                session.nav.go_to_select_org(self.org_name)
                session.nav.go_to_red_hat_subscriptions()
                self.subscriptions.upload(path)
                self.subscriptions.delete()
                success_ele = self.subscriptions.wait_until_element(alert_loc)
                self.assertTrue(success_ele)
        finally:
            manifest.delete_distributor(ds_uuid=mdetails['uuid'])
