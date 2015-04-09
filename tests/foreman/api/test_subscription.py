"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html

"""
from robottelo import entities
from robottelo.common import manifests
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    def test_positive_create_1(self):
        """@Test: Upload a manifest.

        @Assert: Manifest is uploaded successfully

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        org_id = entities.Organization().create()['id']
        entities.Organization(id=org_id).upload_manifest(
            path=cloned_manifest_path
        )

    def test_positive_delete_1(self):
        """@Test: Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        org_id = entities.Organization().create()['id']
        entities.Organization(id=org_id).upload_manifest(
            path=cloned_manifest_path
        )
        entities.Organization(id=org_id).delete_manifest()

    def test_negative_create_1(self):
        """@Test: Upload the same manifest to two organizations.

        @Assert: The manifest is not uploaded to the second organization.

        @Feature: Subscriptions

        """
        manifest_path = manifests.clone()

        # Upload the manifest to one organization.
        org_id = entities.Organization().create_json()['id']
        entities.Organization(id=org_id).upload_manifest(manifest_path)

        # Upload the manifest to a second organization.
        org = entities.Organization()
        org.id = org.create_json()['id']
        org.upload_manifest(manifest_path)
        self.assertEqual([], org.subscriptions())
