"""Unit tests for the ``roles`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/roles.html

"""
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common import decorators
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from fauxfactory import (
    gen_alpha,
    gen_alphanumeric,
    gen_cjk,
    gen_latin1,
    gen_numeric_string,
    gen_utf8,
)
from unittest import TestCase
import ddt
import httplib
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class RoleTestCase(TestCase):
    """Tests for ``api/v2/roles``."""

    @decorators.data(
        gen_alpha,
        gen_alphanumeric,
        gen_cjk,
        gen_latin1,
        gen_numeric_string,
        gen_utf8,
    )
    def test_positive_create_1(self, name_generator):
        """@Test: Create a role with name ``name_generator()``.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.

        """
        if decorators.bz_bug_is_open(1112657) and (
                name_generator is gen_cjk or
                name_generator is gen_latin1 or
                name_generator is gen_utf8):
            self.skipTest('Bugzilla bug 1112657 is open.')
        name = name_generator()
        try:
            role_id = entities.Role(name=name).create()['id']
        except HTTPError as err:
            self.fail(err)  # fail instead of error

        # GET the role and verify it's name.
        self.assertEqual(entities.Role(id=role_id).read_json()['name'], name)

    @decorators.data(
        gen_alpha,
        gen_alphanumeric,
        gen_cjk,
        gen_latin1,
        gen_numeric_string,
        gen_utf8,
    )
    def test_positive_delete_1(self, name_generator):
        """@Test: Delete a role with name ``name_generator()``.

        @Feature: Role

        @Assert: The role cannot be fetched after it is deleted.

        """
        if decorators.bz_bug_is_open(1112657) and (
                name_generator is gen_cjk or
                name_generator is gen_latin1 or
                name_generator is gen_utf8):
            self.skipTest('Bugzilla bug 1112657 is open.')
        name = name_generator()
        try:
            role_id = entities.Role(name=name).create()['id']
        except HTTPError as err:
            self.fail(err)  # fail instead of error

        # DELETE the role and verify that it cannot be fetched
        role = entities.Role(id=role_id)
        role.delete()
        with self.assertRaises(HTTPError):
            role.read_json()

    @decorators.data(
        gen_alpha,
        gen_alphanumeric,
        gen_cjk,
        gen_latin1,
        gen_numeric_string,
        gen_utf8,
    )
    def test_positive_update_1(self, name_generator):
        """@Test: Update a role with and give a name of ``name_generator()``.

        @Feature: Role

        @Assert: The role is updated with the given name.

        """
        if decorators.bz_bug_is_open(1112657) and (
                name_generator is gen_cjk or
                name_generator is gen_latin1 or
                name_generator is gen_utf8):
            self.skipTest('Bugzilla bug 1112657 is open.')
        try:
            role_id = entities.Role().create()['id']
        except HTTPError as err:
            self.fail(err)  # fail instead of error

        role = entities.Role(id=role_id)
        name = name_generator()
        response = client.put(
            role.path(),
            {u'name': name},
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertEqual(role.read_json()['name'], name)

    def test_positive_create_role_with_permissions(self):
        """@Test: Create a filter to add permissions to a selected role

        @Feature: Role and Permissions

        @Assert: Filter should be created with all permissions
        of a selected resource_type

        """
        role_name = gen_alphanumeric()
        try:
            role_attrs = entities.Role(name=role_name).create()
        except HTTPError as err:
            self.fail(err)  # fail instead of error
        path = entities.Role(id=role_attrs['id']).path()

        # GET the role and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], role_name)
        # Get permissions that have a resource_type of ConfigTemplate.
        permissions = client.get(
            entities.Permission().path(),
            auth=get_server_credentials(),
            verify=False,
            data={'resource_type': 'ConfigTemplate'},
        ).json()['results']
        # Create a filter under a selected role with all permissions
        # of a selected resource_type.
        filter_attrs = entities.Filter(
            role=role_attrs['id'],
            permission=[permission['id'] for permission in permissions]
        ).create()
        # Get all permissions from created filter
        permission_names = client.get(
            entities.Filter(id=filter_attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()['permissions']
        get_permissions = [permission_name['name']
                           for permission_name in permission_names]
        real_permissions = [permission['name'] for permission in permissions]

        self.assertListEqual(get_permissions, real_permissions)

    def test_positive_delete_filter_from_role(self):
        """@Test: Delete the filter to remove permissions from a role.

        @Feature: Role and Permissions

        @Assert: Filter should be deleted

        """
        role_name = gen_alphanumeric()
        try:
            role_attrs = entities.Role(name=role_name).create()
        except HTTPError as err:
            self.fail(err)  # fail instead of error
        path = entities.Role(id=role_attrs['id']).path()

        # GET the role and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], role_name)
        # Get permissions that have a resource_type of ConfigTemplate.
        permissions = client.get(
            entities.Permission().path(),
            auth=get_server_credentials(),
            verify=False,
            data={'resource_type': 'Ptable'},
        ).json()['results']

        # Create a filter under a selected role with all permissions
        # of a selected resource_type.
        filter_attrs = entities.Filter(
            role=role_attrs['id'],
            permission=[permission['id'] for permission in permissions]
        ).create()

        # Delete the Filter, GET it, and assert that an HTTP 404 is returned.
        entities.Filter(id=filter_attrs['id']).delete()
        response = client.get(
            entities.Filter(id=filter_attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.NOT_FOUND
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )

    def test_positive_delete_role_inclusive_permissions(self):
        """@Test: Delete a role that includes some permissions.

        @Feature: Role and Permissions

        @Assert: Role as well as inclusive filter should be deleted

        """
        role_name = gen_alphanumeric()
        try:
            role_attrs = entities.Role(name=role_name).create()
        except HTTPError as err:
            self.fail(err)  # fail instead of error
        path = entities.Role(id=role_attrs['id']).path()

        # GET the role and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], role_name)
        # Get permissions that have a resource_type of ConfigTemplate.
        permissions = client.get(
            entities.Permission().path(),
            auth=get_server_credentials(),
            verify=False,
            data={'resource_type': 'Ptable'},
        ).json()['results']

        # Create a filter under a selected role with all permissions
        # of a selected resource_type.
        filter_attrs = entities.Filter(
            role=role_attrs['id'],
            permission=[permission['id'] for permission in permissions]
        ).create()
        filter_path = entities.Filter(id=filter_attrs['id']).path()
        client.get(
            filter_path,
            auth=get_server_credentials(),
            verify=False,
        ).json()

        # Delete the role, GET it, and assert that HTTP 404 is returned for
        # deleted role and filter.
        entities.Role(id=role_attrs['id']).delete()
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.NOT_FOUND
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        # 404 should be returned for deleted filter too
        response = client.get(
            filter_path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.NOT_FOUND
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
