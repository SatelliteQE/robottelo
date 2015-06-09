"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html

"""
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from robottelo.common import manifests
from robottelo.test import APITestCase


class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    def test_positive_create_1(self):
        """@Test: Upload a manifest.

        @Assert: Manifest is uploaded successfully

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        org = entities.Organization().create()
        org.upload_manifest(path=cloned_manifest_path)

    def test_positive_delete_1(self):
        """@Test: Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        org = entities.Organization().create()
        org.upload_manifest(path=cloned_manifest_path)
        self.assertGreater(len(org.subscriptions()), 0)
        org.delete_manifest()
        self.assertEqual(len(org.subscriptions()), 0)

    def test_negative_create_1(self):
        """@Test: Upload the same manifest to two organizations.

        @Assert: The manifest is not uploaded to the second organization.

        @Feature: Subscriptions

        """
        manifest_path = manifests.clone()
        orgs = [entities.Organization().create() for _ in range(2)]
        orgs[0].upload_manifest(manifest_path)
        with self.assertRaises(TaskFailedError):
            orgs[1].upload_manifest(manifest_path)
        self.assertEqual(len(orgs[1].subscriptions()), 0)
