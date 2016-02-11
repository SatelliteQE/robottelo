"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html

"""
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from robottelo.api.utils import upload_manifest
from robottelo import manifests
from robottelo.decorators import skip_if_not_set, tier1
from robottelo.test import APITestCase


class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_create(self):
        """Upload a manifest.

        @Assert: Manifest is uploaded successfully

        @Feature: Subscriptions
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_refresh(self):
        """Upload a manifest and refresh it afterwards.

        @Assert: Manifest is refreshed successfully

        @Feature: Subscriptions
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.original_manifest() as manifest:
            upload_manifest(org.id, manifest.content)
        try:
            sub.refresh_manifest(data={'organization_id': org.id})
            self.assertGreater(len(sub.search()), 0)
        finally:
            sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_delete(self):
        """Delete an Uploaded manifest.

        @Assert: Manifest is Deleted successfully

        @Feature: Subscriptions
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        self.assertGreater(len(sub.search()), 0)
        sub.delete_manifest(data={'organization_id': org.id})
        self.assertEqual(len(sub.search()), 0)

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_negative_upload(self):
        """Upload the same manifest to two organizations.

        @Assert: The manifest is not uploaded to the second organization.

        @Feature: Subscriptions
        """
        orgs = [entities.Organization().create() for _ in range(2)]
        with manifests.clone() as manifest:
            upload_manifest(orgs[0].id, manifest.content)
            with self.assertRaises(TaskFailedError):
                upload_manifest(orgs[1].id, manifest.content)
        self.assertEqual(
            len(entities.Subscription(organization=orgs[1]).search()), 0)
