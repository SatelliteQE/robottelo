# -*- coding: utf-8 -*-
"""Unit tests for the ``permissions`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/permissions.html

"""
import json
import re

from ddt import ddt
from fauxfactory import gen_alphanumeric
from itertools import chain
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.common.constants import PERMISSIONS
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import (
    get_nailgun_config,
    get_server_credentials,
    get_server_software,
)
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@ddt
class PermissionsTestCase(APITestCase):
    """Tests for the ``permissions`` path."""
    @classmethod
    def setUpClass(cls):
        super(PermissionsTestCase, cls).setUpClass()
        cls.permissions = PERMISSIONS.copy()
        if get_server_software() == 'upstream':
            cls.permissions[None].extend(cls.permissions.pop('DiscoveryRule'))
            cls.permissions[None].remove('app_root')
            cls.permissions[None].remove('attachments')
            cls.permissions[None].remove('configuration')
            cls.permissions[None].remove('logs')
            cls.permissions[None].remove('view_cases')
            cls.permissions[None].remove('view_log_viewer')
            cls.permissions[None].remove('view_search')

        #: e.g. ['Architecture', 'Audit', 'AuthSourceLdap', …]
        cls.permission_resource_types = list(cls.permissions.keys())
        #: e.g. ['view_architectures', 'create_architectures', …]
        cls.permission_names = list(
            chain.from_iterable(cls.permissions.values()))

    @run_only_on('sat')
    def test_search_by_name(self):
        """@test: Search for a permission by name.

        @feature: Permissions

        @assert: Only one permission is returned, and the permission returned
        is the one searched for.

        """
        failures = {}
        for permission_name in self.permission_names:
            result = entities.Permission(name=permission_name).search()
            length = len(result)
            name = result[0]['name'] if length > 0 else None
            if length != 1 or permission_name != name:
                failures[permission_name] = {
                    'length': len(result),
                    'returned_name': name,
                }

        if failures:
            self.fail(json.dumps(failures, indent=True, sort_keys=True))

    @run_only_on('sat')
    def test_search_by_resource_type(self):
        """@test: Search for permissions by resource type.

        @feature: Permissions

        @assert: The permissions returned are equal to what is listed for that
        resource type in :data:`robottelo.common.constants.PERMISSIONS`.

        """
        failures = {}
        for resource_type in self.permission_resource_types:
            if resource_type is None:
                continue
            perm_group = entities.Permission(
                resource_type=resource_type).search()
            permissions = set([perm['name'] for perm in perm_group])
            expected_permissions = set(self.permissions[resource_type])
            added = tuple(permissions - expected_permissions)
            removed = tuple(expected_permissions - permissions)

            if added or removed:
                failures[resource_type] = {}
            if added or removed:
                failures[resource_type]['added'] = added
            if removed:
                failures[resource_type]['removed'] = removed

        if failures:
            self.fail(json.dumps(failures, indent=True, sort_keys=True))

    @run_only_on('sat')
    def test_search_permissions(self):
        """@test: search with no parameters return all permissions

        @feature: Permission

        @assert: Search returns a list of all expected permissions

        """
        permissions = entities.Permission().search()
        names = set([perm['name'] for perm in permissions])
        resource_types = set([perm['resource_type'] for perm in permissions])
        expected_names = set(self.permission_names)
        expected_resource_types = set(self.permission_resource_types)

        added_resource_types = tuple(resource_types - expected_resource_types)
        removed_resource_types = tuple(
            expected_resource_types - resource_types)
        added_names = tuple(names - expected_names)
        removed_names = tuple(expected_names - names)

        diff = {}
        if added_resource_types:
            diff['added_resource_types'] = added_resource_types
        if removed_resource_types:
            diff['removed_resource_types'] = removed_resource_types
        if added_names:
            diff['added_names'] = added_names
        if removed_names:
            diff['removed_names'] = removed_names

        if diff:
            self.fail(json.dumps(diff, indent=True, sort_keys=True))


# FIXME: This method is a hack. This information should somehow be tied
# directly to the `Entity` classes.
def _permission_name(entity, which_perm):
    """Find a permission name.

    Attempt to locate a permission in
    :data:`robottelo.common.constants.PERMISSIONS`. For example, return
    'view_architectures' if ``entity`` is ``Architecture`` and ``which_perm``
    is 'read'.

    :param entity: A ``nailgun.entity_mixins.Entity`` subclass.
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
class UserRoleTestCase(APITestCase):
    """Give a user various permissions and see if they are enforced."""

    def setUp(self):  # noqa
        """Create a set of credentials and a user."""
        self.server_config = get_nailgun_config()
        self.server_config.auth = (
            gen_alphanumeric(),  # username
            gen_alphanumeric(),  # password
        )
        self.user = entities.User()
        self.user.id = entities.User(
            login=self.server_config.auth[0],
            password=self.server_config.auth[1],
        ).create_json()['id']

    def give_user_permission(self, perm_name):
        """Give ``self.user`` the ``perm_name`` permission.

        This method creates a role and filter to accomplish the above goal.
        When complete, the relevant relationhips look like this:

            user → role ← filter → permission

        :param str perm_name: The name of a permission. For example:
            'create_architectures'.
        :raises: ``AssertionError`` if more than one permission is found when
            searching for the permission with name ``perm_name``.
        :raises: ``requests.exceptions.HTTPError`` if an error occurs when
            updating ``self.user``'s roles.
        :returns: Nothing.

        """
        role_id = entities.Role().create_json()['id']
        permission_ids = [
            permission['id']
            for permission
            in entities.Permission(name=perm_name).search()
        ]
        self.assertEqual(len(permission_ids), 1)
        entities.Filter(permission=permission_ids, role=role_id).create_json()
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
    def test_create(self, entity_cls):
        """@Test: Check whether the "create_*" role has an effect.

        @Assert: A user cannot create an entity when missing the "create_*"
        role, and they can create an entity when given the "create_*" role.

        @Feature: Role

        """
        with self.assertRaises(HTTPError):
            entity_cls(self.server_config).create_json()
        self.give_user_permission(_permission_name(entity_cls, 'create'))
        entity_id = entity_cls(self.server_config).create_json()['id']
        entity_cls(id=entity_id).read_json()  # read as an admin user

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_read(self, entity_cls):
        """@Test: Check whether the "view_*" role has an effect.

        @Assert: A user cannot read an entity when missing the "view_*" role,
        and they can read an entity when given the "view_*" role.

        @Feature: Role

        """
        entity_id = entity_cls().create_json()['id']
        entity = entity_cls(self.server_config, id=entity_id)
        with self.assertRaises(HTTPError):
            entity.read_json()
        self.give_user_permission(_permission_name(entity_cls, 'read'))
        entity.read_json()

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_delete(self, entity_cls):
        """@Test: Check whether the "destroy_*" role has an effect.

        @Assert: A user cannot read an entity with missing the "destroy_*"
        role, and they can read an entity when given the "destroy_*" role.

        @Feature: Role

        """
        entity_id = entity_cls().create_json()['id']
        entity = entity_cls(self.server_config, id=entity_id)
        with self.assertRaises(HTTPError):
            entity.delete()
        self.give_user_permission(_permission_name(entity_cls, 'delete'))
        entity.delete()
        with self.assertRaises(HTTPError):
            entity.read_json()  # As admin user

    @data(
        entities.Architecture,
        entities.Domain,
    )
    def test_update(self, entity_cls):
        """@Test: Check whether the "edit_*" role has an effect.

        @Assert: A user cannot update an entity when missing the "edit_*" role,
        and they can update an entity when given the "edit_*" role.

        @Feature: Role

        NOTE: This method will only work if ``entity`` has a name.

        """
        entity_id = entity_cls().create_json()['id']
        entity = entity_cls(self.server_config, id=entity_id)
        with self.assertRaises(HTTPError):
            client.put(
                entity.path(),
                {u'name': entity.get_fields()['name'].gen_value()},
                auth=self.server_config.auth,
                verify=self.server_config.verify,
            ).raise_for_status()
        self.give_user_permission(_permission_name(entity_cls, 'update'))
        client.put(
            entity.path(),
            {u'name': entity.get_fields()['name'].gen_value()},
            auth=self.server_config.auth,
            verify=self.server_config.verify,
        ).raise_for_status()
