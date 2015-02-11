"""Unit tests for the ``roles`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/roles.html

"""
from fauxfactory import gen_string
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities, factory, orm
from unittest import TestCase
import ddt
import httplib
import unittest
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class RoleTestCase(TestCase):
    """Tests for ``api/v2/roles``."""
    def _test_role_name(self, name):
        """Create a role with name ``name``."""
        try:
            role_attrs = entities.Role(name=name).create()
        except factory.FactoryError as err:
            self.fail(err)  # fail instead of error

        # Creation apparently succeeded. GET the role and verify it's name.
        response = client.get(
            entities.Role(id=role_attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)

    @ddt.data(
        gen_string('alphanumeric'),
        gen_string('alpha'),
        gen_string('numeric'),
    )
    def test_positive_create_1(self, name):
        """@Test: Create a role with a name containing alphanumeric chars.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.

        """
        self._test_role_name(name)

    @unittest.skip('Note: BZ 1112657 is fixed in upstream but not downstream')
    @ddt.data(
        orm.StringField(str_type=('cjk',)).get_value(),
        orm.StringField(str_type=('latin1',)).get_value(),
        orm.StringField(str_type=('utf8',)).get_value(),
    )
    def test_positive_create_2(self, name):
        """@Test: Create a role with a name containing non-alphanumeric chars.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.

        """
        self._test_role_name(name)

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_delete_1(self, name):
        """@Test: Create a role and delete it

        @Feature: Role

        @Assert: Role deletion should succeed

        """
        try:
            role_attrs = entities.Role(name=name).create()
        except factory.FactoryError as err:
            self.fail(err)  # fail instead of error

        path = entities.Role(id=role_attrs['id']).path()

        # GET the role and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)

        # Delete the role, GET it, and assert that an HTTP 404 is returned.
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

    @ddt.data(
        {u'name': gen_string('alphanumeric'),
         u'new_name': gen_string('alphanumeric')},
        {u'name': gen_string('alpha'), u'new_name': gen_string('alpha')},
        {u'name': gen_string('numeric'), u'new_name': gen_string('numeric')},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Create a role and update its name

        @Feature: Role

        @Assert: Role name should be updated

        """
        try:
            role_attrs = entities.Role(name=test_data['name']).create()
        except factory.FactoryError as err:
            self.fail(err)  # fail instead of error

        path = entities.Role(id=role_attrs['id']).path()

        role_copy = role_attrs.copy()
        role_copy['name'] = test_data['new_name']

        response = client.put(
            path,
            role_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated role
        updated_attrs = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Assert that values have changed
        self.assertNotEqual(
            updated_attrs['name'],
            role_attrs['name'],
        )

    def test_positive_create_role_with_permissions(self):
        """@Test: Create a filter to add permissions to a selected role

        @Feature: Role and Permissions

        @Assert: Filter should be created with all permissions
        of a selected resource_type

        """
        role_name = orm.StringField(str_type=('alphanumeric',)).get_value()

        try:
            role_attrs = entities.Role(name=role_name).create()
        except factory.FactoryError as err:
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
        role_name = orm.StringField(str_type=('alphanumeric',)).get_value()

        try:
            role_attrs = entities.Role(name=role_name).create()
        except factory.FactoryError as err:
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

        # Delete the Filter, GET it, and assert that an HTTP 404 is returned.
        entities.Filter(id=filter_attrs['id']).delete()
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

    def test_positive_delete_role_inclusive_permissions(self):
        """@Test: Delete a role that includes some permissions.

        @Feature: Role and Permissions

        @Assert: Role as well as inclusive filter should be deleted

        """
        role_name = orm.StringField(str_type=('alphanumeric',)).get_value()

        try:
            role_attrs = entities.Role(name=role_name).create()
        except factory.FactoryError as err:
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
