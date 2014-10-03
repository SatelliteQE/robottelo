"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html

"""
from fauxfactory import (
    gen_alpha,
    gen_alphanumeric,
    gen_cjk,
    gen_latin1,
    gen_numeric_string,
    gen_utf8,
)
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.helpers import get_server_credentials
from robottelo.common import decorators
from robottelo import entities
from unittest import TestCase
import ddt
# (too-many-public-methods) pylint:disable=R0904


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
