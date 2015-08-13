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
        org = entities.Organization().create()
        with open(manifests.clone(), 'rb') as manifest:
            entities.Subscription().upload(
                data={'organization_id': org.id},
                files={'content': manifest},
            )

    def test_positive_delete_1(self):
        """@Test: Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions

        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        payload = {'organization_id': org.id}
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload(data=payload, files={'content': manifest})
        self.assertGreater(len(sub.search()), 0)
        sub.delete_manifest(data=payload)
        self.assertEqual(len(sub.search()), 0)

    def test_negative_create_1(self):
        """@Test: Upload the same manifest to two organizations.

        @Assert: The manifest is not uploaded to the second organization.

        @Feature: Subscriptions

        """
        orgs = [entities.Organization().create() for _ in range(2)]
        sub = entities.Subscription()
        with open(manifests.clone(), 'rb') as manifest:
            files = {'content': manifest}
            sub.upload(data={'organization_id': orgs[0].id}, files=files)
            with self.assertRaises(TaskFailedError):
                sub.upload(data={'organization_id': orgs[1].id}, files=files)
        self.assertEqual(
            len(entities.Subscription(organization=orgs[1]).search()), 0)
