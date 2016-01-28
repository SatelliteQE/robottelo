# -*- encoding: utf-8 -*-
"""Unit tests for the Compute Profile feature."""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import APITestCase


class ComputeProfileTestCase(APITestCase):
    """Tests for compute profiles."""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new Compute Profile using different names

        @Feature: Compute Profile - Positive Create

        @Assert: Compute Profile is created
        """
        for name in valid_data_list():
            with self.subTest(name):
                profile = entities.ComputeProfile(name=name).create()
                self.assertEqual(name, profile.name)

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Attempt to create Compute Profile using invalid names only

        @Feature: Compute Profile - Negative Create

        @Assert: Compute Profile is not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(name=name).create()

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update selected Compute Profile entity using proper names

        @Feature: Compute Profile - Positive Update

        @Assert: Compute Profile is updated.
        """
        profile = entities.ComputeProfile().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated_profile = entities.ComputeProfile(
                    id=profile.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated_profile.name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update Compute Profile entity using invalid names only

        @Feature: Compute Profile - Negative Update

        @Assert: Compute Profile is not updated.
        """
        profile = entities.ComputeProfile().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(
                        id=profile.id, name=new_name).update(['name'])
                updated_profile = entities.ComputeProfile(id=profile.id).read()
                self.assertNotEqual(new_name, updated_profile.name)

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete Compute Profile entity

        @Feature: Compute Profile - Positive Delete

        @Assert: Compute Profile is deleted successfully.
        """
        for name in valid_data_list():
            with self.subTest(name):
                profile = entities.ComputeProfile(name=name).create()
                profile.delete()
                with self.assertRaises(HTTPError):
                    entities.ComputeProfile(id=profile.id).read()
