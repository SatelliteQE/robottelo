"""Unit tests for the ``permissions`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/permissions.html

"""
import ddt
import itertools
from robottelo.common.constants import PERMISSIONS
from robottelo.common.decorators import run_only_on
from robottelo import entities
from unittest import TestCase
# (too many public methods) pylint: disable=R0904


PERMISSIONS_RESOURCE_TYPE = [key for key in PERMISSIONS.keys()
                             if key is not None]
PERMISSIONS_NAME = [value for value in itertools.chain(*PERMISSIONS.values())]


@ddt.ddt
class PermissionsTestCase(TestCase):
    """Tests for the ``permissions`` path."""
    @run_only_on('sat')
    @ddt.data(*PERMISSIONS_NAME)
    def test_search_by_name(self, permission_name):
        """@test: permissions can be searched by name

        @feature: Permissions

        @assert: Searched permission name match the query name

        """
        result = entities.Permission(name=permission_name).search()
        self.assertEqual(len(result), 1)
        self.assertEqual(permission_name, result[0]['name'])

    @run_only_on('sat')
    @ddt.data(*PERMISSIONS_RESOURCE_TYPE)
    def test_search_by_resource_type(self, resource_type):
        """@test: permissions can be searched by resource type

        @feature: Permissions - Search

        @assert: Search returns a list of all expected resource_type's
        permissions

        """
        result = entities.Permission(resource_type=resource_type).search()
        permissions = PERMISSIONS[resource_type]
        result_permissions = [permission['name'] for permission in result]
        self.assertEqual(len(result), len(permissions))
        self.assertItemsEqual(permissions, result_permissions)

    @run_only_on('sat')
    def test_search_permissions(self):
        """@test: search with no parameters return all permissions

        @feature: Permission - Search

        @assert: Search returns a list of all expected permissions

        """
        result = entities.Permission().search()
        result_name = [permission['name'] for permission in result]
        self.assertItemsEqual(PERMISSIONS_NAME, result_name)
