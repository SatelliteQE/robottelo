"""Test class for Subscriptions"""

from ddt import ddt
from robottelo.cli.subscription import Subscription
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.factory import make_org
from robottelo.common.manifests import clone
from robottelo.common.ssh import upload_file
from robottelo.test import CLITestCase


@ddt
class TestSubscription(CLITestCase):
    """Manifest CLI tests"""
    signing_key = None
    fake_manifest = None

    def setUp(self):
        """Tests for content-view via Hammer CLI"""

        super(TestSubscription, self).setUp()
        self.org = make_org()
        self.manifest = clone()

    def test_manifest_upload(self):
        """@Test: upload manifest (positive)

        @Feature: Subscriptions/Manifest Upload

        @Assert: Manifest are uploaded properly

        """

        upload_file(self.manifest, remote_file=self.manifest)
        result = Subscription.upload({
            'file': self.manifest,
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "Failed to upload manifest")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while uploading manifest.")

        result = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False)
        self.assertEqual(result.return_code, 0,
                         "Failed to list manifests in this org.")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while listing the manifest.")

    def test_manifest_delete(self):
        """@Test: Delete uploaded manifest (positive)

        @Feature: Subscriptions/Manifest Delete

        @Assert: Manifest are deleted properly
        """

        upload_file(self.manifest, remote_file=self.manifest)
        result = Subscription.upload({
            'file': self.manifest,
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "Failed to upload manifest")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while uploading manifest.")

        result = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False)
        self.assertEqual(result.return_code, 0,
                         "Failed to list manifests in this org.")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while listing the manifest.")

        result = Subscription.delete_manifest({
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "Failed to delete manifest")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while deleting manifest.")

        result = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False)
        self.assertEqual(result.return_code, 0,
                         "Failed to list manifests in this org.")
        self.assertEqual(
            len(result.stdout), 0,
            "There should not be any subscriptions in this org.")

    def test_enable_manifest_repository_set(self):
        """@Test: enable repository set (positive)

        @Feature: Subscriptions/Repository Sets

        @Assert: you are able to enable and synchronize
        repository contained in a manifest

        """

        upload_file(self.manifest, remote_file=self.manifest)
        result = Subscription.upload({
            'file': self.manifest,
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "Failed to upload manifest")
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while uploading manifest.")

        result = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False)
        self.assertEqual(
            len(result.stderr), 0,
            "There should not be an exception while listing the manifest.")

        result = RepositorySet.enable({
            'name': (
                'Red Hat Enterprise Virtualization Agents '
                'for RHEL 6 Workstation (RPMs)'
            ),
            'organization-id': self.org['id'],
            'product': 'Red Hat Enterprise Linux Workstation',
            'releasever': '6Workstation',
            'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0, "Repo was not enabled")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = Repository.synchronize({
            'name': (
                'Red Hat Enterprise Virtualization Agents '
                'for RHEL 6 Workstation '
                'RPMs x86_64 6Workstation'
            ),
            'organization-id': self.org['id'],
            'product': 'Red Hat Enterprise Linux Workstation',
        })

        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
