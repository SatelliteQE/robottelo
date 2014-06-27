"""
Test class for Subscriptions
"""

from ddt import ddt
from robottelo.cli.subscription import Subscription
from robottelo.cli.factory import (
    make_org, make_lifecycle_environment)
from robottelo.common.decorators import stubbed
from robottelo.common.manifests import manifest
from robottelo.common.ssh import upload_file
from robottelo.test import CLITestCase


@ddt
class TestSubscription(CLITestCase):
    """
    Manifest CLI tests
    """

    org = None
    env1 = None
    env2 = None

    def setUp(self):
        """
        Tests for content-view via Hammer CLI
        """

        super(TestSubscription, self).setUp()

        if TestSubscription.org is None:
            TestSubscription.org = make_org()
        if TestSubscription.env1 is None:
            TestSubscription.env1 = make_lifecycle_environment(
                {u'organization-id': TestSubscription.org['id']})
        if TestSubscription.env2 is None:
            TestSubscription.env2 = make_lifecycle_environment(
                {u'organization-id': TestSubscription.org['id'],
                 u'prior': TestSubscription.env1['label']})

    @stubbed('Need to implement a new manifest api')
    def test_manifest_upload(self):
        """
        @test: upload manifest (positive)
        @feature: Subscriptions/Manifest Upload
        @assert: Manifest are uploaded properly
        """

        mdetails = manifest.fetch_manifest()
        try:
            upload_file(mdetails['path'], remote_file=mdetails['path'])
            result = Subscription.upload(
                {'file': mdetails['path'],
                 'organization-id': self.org['id']})
            self.assertEqual(result.return_code, 0,
                             "Failed to upload manifest")
            self.assertEqual(
                len(result.stderr), 0,
                "There should not be an exception while uploading manifest.")

            result = Subscription.list({'organization-id': self.org['id']},
                                       per_page=False)
            self.assertEqual(result.return_code, 0,
                             "Failed to list manifests in this org.")
            self.assertEqual(
                len(result.stdout), 8,
                "There should not be an exception while listing the manifest.")
        finally:
            manifest.delete_distributor(ds_uuid=mdetails['uuid'])

    @stubbed('Need to implement a new manifest api')
    def test_manifest_delete(self):
        """
        @test: Delete uploaded manifest (positive)
        @feature: Subscriptions/Manifest Delete
        @assert: Manifest are deleted properly
        """

        mdetails = manifest.fetch_manifest()
        try:
            upload_file(mdetails['path'], remote_file=mdetails['path'])
            result = Subscription.upload(
                {'file': mdetails['path'],
                 'organization-id': self.org['id']})
            self.assertEqual(result.return_code, 0,
                             "Failed to upload manifest")
            self.assertEqual(
                len(result.stderr), 0,
                "There should not be an exception while uploading manifest.")

            result = Subscription.list({'organization-id': self.org['id']},
                                       per_page=False)
            self.assertEqual(result.return_code, 0,
                             "Failed to list manifests in this org.")
            self.assertEqual(
                len(result.stdout), 8,
                "There should not be an exception while listing the manifest.")

            result = Subscription.delete_manifest(
                {'organization-id': self.org['id']})
            self.assertEqual(result.return_code, 0,
                             "Failed to delete manifest")
            self.assertEqual(
                len(result.stderr), 0,
                "There should not be an exception while deleting manifest.")

            result = Subscription.list({'organization-id': self.org['id']},
                                       per_page=False)
            self.assertEqual(result.return_code, 0,
                             "Failed to list manifests in this org.")
            self.assertEqual(
                len(result.stdout), 0,
                "There should not be any subscriptions in this org.")
        finally:
            manifest.delete_distributor(ds_uuid=mdetails['uuid'])
