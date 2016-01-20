# -*- coding: utf-8 -*-
"""Unit tests for the ``permissions`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/permissions.html

"""
import json
import re

from fauxfactory import gen_alphanumeric
from itertools import chain
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import PERMISSIONS
from robottelo.decorators import run_only_on, tier1
from robottelo.helpers import get_nailgun_config, get_server_software
from robottelo.test import APITestCase


class PermissionTestCase(APITestCase):
    """Tests for the ``permissions`` path."""
    @classmethod
    def setUpClass(cls):
        super(PermissionTestCase, cls).setUpClass()
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
    @tier1
    def test_positive_search_by_name(self):
        """Search for a permission by name.

        @feature: Permissions

        @assert: Only one permission is returned, and the permission returned
        is the one searched for.
        """
        failures = {}
        for permission_name in self.permission_names:
            results = entities.Permission(name=permission_name).search()
            if (len(results) != 1 or
                    len(results) == 1 and results[0].name != permission_name):
                failures[permission_name] = {
                    'length': len(results),
                    'returned_names': [result.name for result in results]
                }

        if failures:
            self.fail(json.dumps(failures, indent=True, sort_keys=True))

    @run_only_on('sat')
    @tier1
    def test_positive_search_by_resource_type(self):
        """Search for permissions by resource type.

        @feature: Permissions

        @assert: The permissions returned are equal to what is listed for that
        resource type in :data:`robottelo.constants.PERMISSIONS`.
        """
        failures = {}
        for resource_type in self.permission_resource_types:
            if resource_type is None:
                continue
            perm_group = entities.Permission(
                resource_type=resource_type).search()
            permissions = {perm.name for perm in perm_group}
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
    @tier1
    def test_positive_search(self):
        """search with no parameters return all permissions

        @feature: Permission

        @assert: Search returns a list of all expected permissions
        """
        permissions = entities.Permission().search(query={'per_page': 1000})
        names = {perm.name for perm in permissions}
        resource_types = {perm.resource_type for perm in permissions}
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

    Attempt to locate a permission in :data:`robottelo.constants.PERMISSIONS`.
    For example, return 'view_architectures' if ``entity`` is ``Architecture``
    and ``which_perm`` is 'read'.

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
class UserRoleTestCase(APITestCase):
    """Give a user various permissions and see if they are enforced."""

    def setUp(self):  # noqa
        """Create a set of credentials and a user."""
        self.cfg = get_nailgun_config()
        self.cfg.auth = (gen_alphanumeric(), gen_alphanumeric())  # user, pass
        self.user = entities.User(
            login=self.cfg.auth[0],
            password=self.cfg.auth[1],
        ).create()

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
        role = entities.Role().create()
        permissions = entities.Permission(name=perm_name).search()
        self.assertEqual(len(permissions), 1)
        entities.Filter(permission=permissions, role=role).create()
        self.user.role = [role]
        self.user = self.user.update(['role'])

    @tier1
    def test_positive_check_create(self):
        """Check whether the "create_*" role has an effect.

        @Assert: A user cannot create an entity when missing the "create_*"
        role, and they can create an entity when given the "create_*" role.

        @Feature: Role
        """
        for entity_cls in (entities.Architecture, entities.Domain):
            with self.subTest(entity_cls):
                with self.assertRaises(HTTPError):
                    entity_cls(self.cfg).create()
                self.give_user_permission(
                    _permission_name(entity_cls, 'create')
                )
                entity_id = entity_cls(self.cfg).create_json()['id']
                entity_cls(id=entity_id).read()  # As admin user.

    @tier1
    def test_positive_check_read(self):
        """Check whether the "view_*" role has an effect.

        @Assert: A user cannot read an entity when missing the "view_*" role,
        and they can read an entity when given the "view_*" role.

        @Feature: Role

        """
        for entity_cls in (entities.Architecture, entities.Domain):
            with self.subTest(entity_cls):
                entity_id = entity_cls().create().id
                with self.assertRaises(HTTPError):
                    entity_cls(self.cfg, id=entity_id).read()
                self.give_user_permission(_permission_name(entity_cls, 'read'))
                entity_cls(self.cfg, id=entity_id).read()

    @tier1
    def test_positive_check_delete(self):
        """Check whether the "destroy_*" role has an effect.

        @Assert: A user cannot read an entity with missing the "destroy_*"
        role, and they can read an entity when given the "destroy_*" role.

        @Feature: Role

        """
        for entity_cls in (entities.Architecture, entities.Domain):
            with self.subTest(entity_cls):
                entity = entity_cls().create()
                with self.assertRaises(HTTPError):
                    entity_cls(self.cfg, id=entity.id).delete()
                self.give_user_permission(
                    _permission_name(entity_cls, 'delete')
                )
                entity_cls(self.cfg, id=entity.id).delete()
                with self.assertRaises(HTTPError):
                    entity.read()  # As admin user

    @tier1
    def test_positive_check_update(self):
        """Check whether the "edit_*" role has an effect.

        @Assert: A user cannot update an entity when missing the "edit_*" role,
        and they can update an entity when given the "edit_*" role.

        @Feature: Role

        NOTE: This method will only work if ``entity`` has a name.

        """
        for entity_cls in (entities.Architecture, entities.Domain):
            with self.subTest(entity_cls):
                entity = entity_cls().create()
                name = entity.get_fields()['name'].gen_value()
                with self.assertRaises(HTTPError):
                    entity_cls(self.cfg, id=entity.id, name=name).update(
                        ['name']
                    )
                self.give_user_permission(
                    _permission_name(entity_cls, 'update')
                )
                # update() calls read() under the hood, which triggers
                # permission error
                entity_cls(self.cfg, id=entity.id, name=name).update_json(
                    ['name']
                )
