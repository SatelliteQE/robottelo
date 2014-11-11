"""Unit tests for the ``filters`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/filters.html

"""
from requests.exceptions import HTTPError
from robottelo import entities
from unittest import TestCase
# (too-many-public-methods) pylint:disable=R0904


class FilterTestCase(TestCase):
    """Tests for ``api/v2/filters``."""
    _multiprocess_can_split_ = True

    def test_create_filter_with_perms(self):
        """@Test: Create a filter and assign it some permissions.

        @Assert: The created filter has the assigned permissions.

        @Feature: Filter

        """
        # Create a filter and assign all ConfigTemplate permissions to it.
        ct_perms = entities.Permission(resource_type='ConfigTemplate').search()
        filter_id = entities.Filter(
            permission=[
                permission['id']
                for permission
                in ct_perms
            ]
        ).create()['id']

        # Find all permissions assigned to filter `filter_id`.
        filter_perms = entities.Filter(id=filter_id).read_json()['permissions']
        self.assertListEqual(ct_perms, filter_perms)

    def test_directly_delete_filter(self):
        """@Test: Create a filter and delete it.

        @Assert: The deleted filter cannot be feched.

        @Feature: Filter

        """
        filter_ = entities.Filter(id=entities.Filter(
            permission=[
                permission['id']
                for permission
                in entities.Permission(resource_type='ConfigTemplate').search()
            ],
        ).create()['id'])
        filter_.delete()
        with self.assertRaises(HTTPError):
            filter_.read_json()

    def test_implicitly_delete_filter(self):
        """@Test: Create a filter and delete the role it points at.

        @Assert: The filter cannot be fetched.

        @Feature: Filter

        """
        role = entities.Role(id=entities.Role().create()['id'])
        ct_perms = entities.Permission(resource_type='ConfigTemplate').search()
        filter_ = entities.Filter(id=entities.Filter(
            permission=[permission['id'] for permission in ct_perms],
            role=role.id,
        ).create()['id'])

        # A filter depends on a role. Deleting a role implicitly deletes the
        # filter pointing at it.
        role.delete()
        with self.assertRaises(HTTPError):
            role.read_json()
        with self.assertRaises(HTTPError):
            filter_.read_json()
