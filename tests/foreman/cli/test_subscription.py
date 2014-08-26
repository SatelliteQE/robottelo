"""
Test class for Subscriptions
"""

import tempfile

from ddt import ddt
from robottelo.cli.subscription import Subscription
from robottelo.cli.factory import make_org
from robottelo.common.manifests import (
    clone, download_signing_key,
    download_manifest_template, install_cert_on_server)
from robottelo.common.ssh import upload_file
from robottelo.test import CLITestCase


@ddt
class TestSubscription(CLITestCase):
    """
    Manifest CLI tests
    """
    signing_key = None
    fake_manifest = None

    def setUp(self):
        """
        Tests for content-view via Hammer CLI
        """

        super(TestSubscription, self).setUp()

        if TestSubscription.signing_key is None:
            TestSubscription.signing_key = download_signing_key()
            TestSubscription.fake_manifest = download_manifest_template()
            install_cert_on_server()

        self.org = make_org()
        manifest_file = tempfile.mktemp()
        clone(
            TestSubscription.signing_key,
            TestSubscription.fake_manifest,
            manifest_file)
        self.manifest = manifest_file

    def test_manifest_upload(self):
        """
        @test: upload manifest (positive)
        @feature: Subscriptions/Manifest Upload
        @assert: Manifest are uploaded properly
        """

        upload_file(self.manifest, remote_file=self.manifest)
        result = Subscription.upload(
            {'file': self.manifest,
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
            len(result.stderr), 0,
            "There should not be an exception while listing the manifest.")

    def test_manifest_delete(self):
        """
        @test: Delete uploaded manifest (positive)
        @feature: Subscriptions/Manifest Delete
        @assert: Manifest are deleted properly
        """

        upload_file(self.manifest, remote_file=self.manifest)
        result = Subscription.upload(
            {'file': self.manifest,
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
            len(result.stderr), 0,
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
