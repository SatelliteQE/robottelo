"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html


:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from robottelo.api.utils import upload_manifest
from robottelo import manifests
from robottelo.decorators import (
    run_in_one_thread, skip_if_not_set, tier1, tier2
)
from robottelo.test import APITestCase


@run_in_one_thread
class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_create(self):
        """Upload a manifest.

        :id: 6faf9d96-9b45-4bdc-afa9-ec3fbae83d41

        :expectedresults: Manifest is uploaded successfully

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_refresh(self):
        """Upload a manifest and refresh it afterwards.

        :id: cd195db6-e81b-42cb-a28d-ec0eb8a53341

        :expectedresults: Manifest is refreshed successfully

        :CaseImportance: Critical
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
    def test_positive_create_after_refresh(self):
        """Upload a manifest,refresh it and upload a new manifest to an other
         organization.

        :id: 1869bbb6-c31b-49a9-bc92-402a90071a11

        :customerscenario: true

        :expectedresults: the manifest is uploaded successfully to other org

        :BZ: 1393442

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        org_sub = entities.Subscription(organization=org)
        new_org = entities.Organization().create()
        new_org_sub = entities.Subscription(organization=new_org)
        self.upload_manifest(org.id, manifests.original_manifest())
        try:
            org_sub.refresh_manifest(data={'organization_id': org.id})
            self.assertGreater(len(org_sub.search()), 0)
            self.upload_manifest(new_org.id, manifests.clone())
            self.assertGreater(len(new_org_sub.search()), 0)
        finally:
            org_sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_delete(self):
        """Delete an Uploaded manifest.

        :id: 4c21c7c9-2b26-4a65-a304-b978d5ba34fc

        :expectedresults: Manifest is Deleted successfully

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        self.assertGreater(len(sub.search()), 0)
        sub.delete_manifest(data={'organization_id': org.id})
        self.assertEqual(len(sub.search()), 0)

    @skip_if_not_set('fake_manifest')
    @tier2
    def test_negative_upload(self):
        """Upload the same manifest to two organizations.

        :id: 60ca078d-cfaf-402e-b0db-34d8901449fe

        :expectedresults: The manifest is not uploaded to the second
            organization.
        """
        orgs = [entities.Organization().create() for _ in range(2)]
        with manifests.clone() as manifest:
            upload_manifest(orgs[0].id, manifest.content)
            with self.assertRaises(TaskFailedError):
                upload_manifest(orgs[1].id, manifest.content)
        self.assertEqual(
            len(entities.Subscription(organization=orgs[1]).search()), 0)
