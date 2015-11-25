"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html

"""
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from robottelo.api.utils import upload_manifest
from robottelo import manifests
from robottelo.decorators import tier1
from robottelo.test import APITestCase


class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    @tier1
    def test_positive_create_1(self):
        """@Test: Upload a manifest.

        @Assert: Manifest is uploaded successfully

        @Feature: Subscriptions

        """
        org = entities.Organization().create()
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)

    @tier1
    def test_positive_delete_1(self):
        """@Test: Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions

        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)
        self.assertGreater(len(sub.search()), 0)
        sub.delete_manifest(data={'organization_id': org.id})
        self.assertEqual(len(sub.search()), 0)

    @tier1
    def test_negative_create_1(self):
        """@Test: Upload the same manifest to two organizations.

        @Assert: The manifest is not uploaded to the second organization.

        @Feature: Subscriptions

        """
        orgs = [entities.Organization().create() for _ in range(2)]
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(orgs[0].id, manifest)
            with self.assertRaises(TaskFailedError):
                upload_manifest(orgs[1].id, manifest)
        self.assertEqual(
            len(entities.Subscription(organization=orgs[1]).search()), 0)
