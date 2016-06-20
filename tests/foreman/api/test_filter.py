"""Unit tests for the ``filters`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/filters.html


@Requirement: Filter

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
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

        @id: b8631d0a-a71a-41aa-9f9a-d12d62adc496

        @Assert: The created filter has the assigned permissions.
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

        @id: f0c56fd8-c91d-48c3-ad21-f538313b17eb

        @Assert: The deleted filter cannot be fetched.
        """
        filter_ = entities.Filter(permission=self.ct_perms).create()
        filter_.delete()
        with self.assertRaises(HTTPError):
            filter_.read()

    @tier1
    def test_positive_delete_role(self):
        """Create a filter and delete the role it points at.

        @id: b129642d-926d-486a-84d9-5952b44ac446

        @Assert: The filter cannot be fetched.
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
