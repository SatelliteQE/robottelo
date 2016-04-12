"""Unit tests for the ``filters`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/filters.html

"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.decorators import tier1
from robottelo.test import APITestCase


class FilterTestCase(APITestCase):
    """Tests for ``api/v2/filters``."""

    @classmethod
    def setUpClass(cls):
        """Search for provisioning template permissions. Set ``cls.ct_perms``.
        """
        super(FilterTestCase, cls).setUpClass()
        cls.ct_perms = (
            entities.Permission(resource_type='ProvisioningTemplate').search()
        )

    @tier1
    def test_positive_create_with_permission(self):
        """Create a filter and assign it some permissions.

        @Assert: The created filter has the assigned permissions.

        @Feature: Filter
        """
        # Create a filter and assign all ProvisioningTemplate permissions to it
        filter_ = entities.Filter(permission=self.ct_perms).create()
        self.assertListEqual(
            [perm.id for perm in filter_.permission],
            [perm.id for perm in self.ct_perms],
        )

    @tier1
    def test_positive_delete(self):
        """Create a filter and delete it afterwards.

        @Assert: The deleted filter cannot be fetched.

        @Feature: Filter
        """
        filter_ = entities.Filter(permission=self.ct_perms).create()
        filter_.delete()
        with self.assertRaises(HTTPError):
            filter_.read()

    @tier1
    def test_positive_delete_role(self):
        """Create a filter and delete the role it points at.

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
