"""Unit tests for the ``filters`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/filters.html

"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.test import APITestCase


class FilterTestCase(APITestCase):
    """Tests for ``api/v2/filters``."""

    @classmethod
    def setUpClass(cls):
        """Search for config template permissions. Set ``cls.ct_perms``."""
        super(FilterTestCase, cls).setUpClass()
        cls.ct_perms = (
            entities.Permission(resource_type='ConfigTemplate').search()
        )

    def test_create_filter_with_perms(self):
        """@Test: Create a filter and assign it some permissions.

        @Assert: The created filter has the assigned permissions.

        @Feature: Filter

        """
        # Create a filter and assign all ConfigTemplate permissions to it.
        filter_ = entities.Filter(permission=self.ct_perms).create()
        self.assertListEqual(
            [perm.id for perm in filter_.permission],
            [perm.id for perm in self.ct_perms],
        )

    def test_directly_delete_filter(self):
        """@Test: Create a filter and delete it.

        @Assert: The deleted filter cannot be feched.

        @Feature: Filter

        """
        filter_ = entities.Filter(permission=self.ct_perms).create()
        filter_.delete()
        with self.assertRaises(HTTPError):
            filter_.read()

    def test_implicitly_delete_filter(self):
        """@Test: Create a filter and delete the role it points at.

        @Assert: The filter cannot be fetched.

        @Feature: Filter

        """
        role = entities.Role().create()
        filter_ = entities.Filter(permission=self.ct_perms, role=role).create()

        # A filter depends on a role. Deleting a role implicitly deletes the
        # filter pointing at it.
        role.delete()
        with self.assertRaises(HTTPError):
            role.read()
        with self.assertRaises(HTTPError):
            filter_.read()
