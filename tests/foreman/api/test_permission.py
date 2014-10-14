"""Unit tests for the ``permissions`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/permissions.html

"""
from ddt import data as ddt_data, ddt
from fauxfactory import gen_alphanumeric
from itertools import chain
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.constants import PERMISSIONS
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import re
# (too-many-public-methods) pylint:disable=R0904


PERMISSIONS_RESOURCE_TYPE = [
    key for key in PERMISSIONS.keys() if key is not None
]
PERMISSIONS_NAME = [
    value for value in chain.from_iterable(PERMISSIONS.values())
]


@ddt
class PermissionsTestCase(TestCase):
    """Tests for the ``permissions`` path."""
    @run_only_on('sat')
    @ddt_data(*PERMISSIONS_NAME)  # pylint:disable=W0142
    def test_search_by_name(self, permission_name):
        """@test: permissions can be searched by name

        @feature: Permissions

        @assert: Searched permission name match the query name

        """
        result = entities.Permission(name=permission_name).search()
        self.assertEqual(len(result), 1)
        self.assertEqual(permission_name, result[0]['name'])

    @run_only_on('sat')
    @ddt_data(*PERMISSIONS_RESOURCE_TYPE)  # pylint:disable=W0142
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


# FIXME: This method is a hack. This information should somehow be tied
# directly to the `Entity` classes.
def _permission_name(entity, which_perm):
    """Find a permission name.

    Attempt to locate a permission in
    :data:`robottelo.common.constants.PERMISSIONS`. For example, return
    'view_architectures' if ``entity`` is ``Architecture`` and ``which_perm``
    is 'read'.

    :param robottelo.orm.Entity entity: An ``Entity`` subclass.
    :param str which_perm: Either the word "create", "read", "update" or
        "delete".
    :raise: ``LookupError`` if a relevant permission cannot be found, or if
        multiple results are found.

    """
    pattern = {
        'create': '^create_',
        'delete': '^destroy_',
        'read': '^view_',
        'update': '^edit_',
    }[which_perm]
    perm_names = []
    for permission in PERMISSIONS[entity.__name__]:
        match = re.match(pattern, permission)
        if match is not None:
            perm_names.append(permission)
    if len(perm_names) != 1:
        raise LookupError(
            'Could not find the requested permission. Found: {0}'
            .format(perm_names)
        )
    return perm_names[0]


# This class might better belong in module test_multiple_paths.
@ddt
class UserRoleTestCase(TestCase):
    """Give a user various permissions and see if they are enforced."""

    def setUp(self):
        """Create a set of credentials and a user."""
        self.auth = (gen_alphanumeric(), gen_alphanumeric())  # login, password
        self.user = entities.User(
            id=entities.User(
                login=self.auth[0],
                password=self.auth[1]
            ).create()['id']
        )

    def give_user_permission(self, perm_name):
        """Give ``self.user`` the ``perm_name`` permission.

        This method creates a role and filter to accomplish the above goal.
        When complete, the relevant relationhips look like this:

            user -> role <- filter -> permission

        :param str perm_name: The name of a permission. For example:
            'create_architectures'.
        :raises: ``AssertionError`` if more than one permission is found when
            searching for the permission with name ``perm_name``.
        :raises: ``requests.exceptions.HTTPError`` if an error occurs when
            updating ``self.user``'s roles.
        :rtype: None

        """
        role_id = entities.Role().create()['id']
        permission_ids = [
            permission['id']
            for permission
            in entities.Permission(name=perm_name).search()
        ]
        self.assertEqual(len(permission_ids), 1)
        entities.Filter(permission=permission_ids, role=role_id).create()
        # NOTE: An extra hash is used due to an API bug.
        client.put(
            self.user.path(),
            {u'user': {u'role_ids': [role_id]}},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_create(self, entity):
        """@Test: Check whether the "create_*" role has an effect.

        @Assert: A user cannot create an entity when missing the "create_*"
        role, and they can create an entity when given the "create_*" role.

        @Feature: Role

        """
        with self.assertRaises(HTTPError):
            entity().create(auth=self.auth)
        self.give_user_permission(_permission_name(entity, 'create'))
        entity_id = entity().create(auth=self.auth)['id']
        entity(id=entity_id).read_json()  # read as an admin user

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_read(self, entity):
        """@Test: Check whether the "view_*" role has an effect.

        @Assert: A user cannot read an entity when missing the "view_*" role,
        and they can read an entity when given the "view_*" role.

        @Feature: Role

        """
        entity_obj = entity(id=entity().create()['id'])
        with self.assertRaises(HTTPError):
            entity_obj.read_json(auth=self.auth)
        self.give_user_permission(_permission_name(entity, 'read'))
        entity_obj.read_json(auth=self.auth)

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_delete(self, entity):
        """@Test: Check whether the "destroy_*" role has an effect.

        @Assert: A user cannot read an entity with missing the "destroy_*"
        role, and they can read an entity when given the "destroy_*" role.

        @Feature: Role

        """
        entity_obj = entity(id=entity().create()['id'])
        with self.assertRaises(HTTPError):
            entity_obj.delete(auth=self.auth)
        self.give_user_permission(_permission_name(entity, 'delete'))
        entity_obj.delete(auth=self.auth)
        with self.assertRaises(HTTPError):
            entity_obj.read_json()  # As admin user

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_update(self, entity):
        """@Test: Check whether the "edit_*" role has an effect.

        @Assert: A user cannot update an entity when missing the "edit_*" role,
        and they can update an entity when given the "edit_*" role.

        @Feature: Role

        NOTE: This method will only work if ``entity`` has a name.

        """
        entity_obj = entity(id=entity().create()['id'])
        with self.assertRaises(HTTPError):
            client.put(
                entity_obj.path(),
                {u'name': entity.name.get_value()},
                auth=self.auth,
                verify=False,
            ).raise_for_status()
        self.give_user_permission(_permission_name(entity, 'update'))
        client.put(
            entity_obj.path(),
            {u'name': entity.name.get_value()},
            auth=self.auth,
            verify=False,
        ).raise_for_status()
