# -*- encoding: utf-8 -*-
"""Unit tests for the Compute Profile feature.

:Requirement: Computeprofile

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import tier1
from robottelo.test import APITestCase


class ComputeProfileTestCase(APITestCase):
    """Tests for compute profiles."""

    @tier1
    def test_positive_create_with_name(self):
        """Create new Compute Profile using different names

        :id: 97d04911-9368-4674-92c7-1e3ff114bc18

        :expectedresults: Compute Profile is created

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        for name in valid_data_list():
            with self.subTest(name):
                profile = entities.ComputeProfile(name=name).create()
                self.assertEqual(name, profile.name)

    @tier1
    def test_negative_create(self):
        """Attempt to create Compute Profile using invalid names only

        :id: 2d34a1fd-70a5-4e59-b2e2-86fbfe8e31ab

        :expectedresults: Compute Profile is not created

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """Update selected Compute Profile entity using proper names

        :id: c79193d7-2e0f-4ed9-b947-05feeddabfda

        :expectedresults: Compute Profile is updated.

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        profile = entities.ComputeProfile().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated_profile = entities.ComputeProfile(
                    id=profile.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated_profile.name)

    @tier1
    def test_negative_update_name(self):
        """Attempt to update Compute Profile entity using invalid names only

        :id: 042b40d5-a78b-4e65-b5cb-5b270b800b37

        :expectedresults: Compute Profile is not updated.

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        profile = entities.ComputeProfile().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(
                        id=profile.id, name=new_name).update(['name'])
                updated_profile = entities.ComputeProfile(id=profile.id).read()
                self.assertNotEqual(new_name, updated_profile.name)

    @tier1
    def test_positive_delete(self):
        """Delete Compute Profile entity

        :id: 0a620e23-7ba6-4178-af7a-fd1e332f478f

        :expectedresults: Compute Profile is deleted successfully.

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        for name in valid_data_list():
            with self.subTest(name):
                profile = entities.ComputeProfile(name=name).create()
                profile.delete()
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(id=profile.id).read()
