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
        task_result = entities.Organization(id=org_id).upload_manifest(
            path=cloned_manifest_path
        )['result']
        self.assertEqual(u'success', task_result)

    def test_positive_delete_1(self):
        """@Test: Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        org_id = entities.Organization().create()['id']
        task_result = entities.Organization(
            id=org_id
        ).upload_manifest(path=cloned_manifest_path)['result']
        self.assertEqual(u'success', task_result)
        task_result = entities.Organization(
            id=org_id
        ).delete_manifest()['result']
        self.assertEqual(u'success', task_result)

    def test_negative_create_1(self):
        """@Test: Upload same manifest to 2 different Organizations.

        @Assert: Manifest is not uploaded in the second Organization.

        @Feature: Subscriptions

        """
        cloned_manifest_path = manifests.clone()
        orgid_one = entities.Organization().create()['id']
        orgid_two = entities.Organization().create()['id']
        task_result1 = entities.Organization(
            id=orgid_one
        ).upload_manifest(path=cloned_manifest_path)['result']
        self.assertEqual(u'success', task_result1)
        task_result2 = entities.Organization(
            id=orgid_two
        ).upload_manifest(path=cloned_manifest_path)['result']
        self.assertNotEqual(u'success', task_result2)
