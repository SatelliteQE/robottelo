"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html

"""
import ddt

from fauxfactory import (
    gen_alpha,
    gen_alphanumeric,
    gen_cjk,
    gen_latin1,
    gen_numeric_string,
    gen_utf8,
)
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo import decorators
from robottelo.test import APITestCase


@ddt.ddt
class RoleTestCase(APITestCase):
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
        self.assertEqual(entities.Role(name=name).create().name, name)

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
        role = entities.Role(name=name).create()
        self.assertEqual(role.name, name)
        role.delete()
        with self.assertRaises(HTTPError):
            role.read()

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
        role = entities.Role().create()
        name = name_generator()
        role.name = name
        self.assertEqual(role.update(['name']).name, name)
