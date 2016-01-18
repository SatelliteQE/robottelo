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
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.decorators import bz_bug_is_open, tier1
from robottelo.test import APITestCase


def data_generator():
    """Returns a tuple of data for role names"""
    return (
        gen_alpha,
        gen_alphanumeric,
        gen_cjk,
        gen_latin1,
        gen_numeric_string,
        gen_utf8,
    )


class RoleTestCase(APITestCase):
    """Tests for ``api/v2/roles``."""

    @tier1
    def test_positive_create(self):
        """Create a role with name ``name_generator()``.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.
        """
        for name_generator in data_generator():
            with self.subTest(name_generator):
                if bz_bug_is_open(1112657) and (
                        name_generator is gen_cjk or
                        name_generator is gen_latin1 or
                        name_generator is gen_utf8):
                    self.skipTest('Bugzilla bug 1112657 is open.')
                name = name_generator()
                self.assertEqual(entities.Role(name=name).create().name, name)

    @tier1
    def test_positive_delete(self):
        """Delete a role with name ``name_generator()``.

        @Feature: Role

        @Assert: The role cannot be fetched after it is deleted.
        """
        for name_generator in data_generator():
            with self.subTest(name_generator):
                if bz_bug_is_open(1112657) and (
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

    @tier1
    def test_positive_update(self):
        """Update a role with and give a name of ``name_generator()``.

        @Feature: Role

        @Assert: The role is updated with the given name.
        """
        for name_generator in data_generator():
            with self.subTest(name_generator):
                if bz_bug_is_open(1112657) and (
                        name_generator is gen_cjk or
                        name_generator is gen_latin1 or
                        name_generator is gen_utf8):
                    self.skipTest('Bugzilla bug 1112657 is open.')
                role = entities.Role().create()
                name = name_generator()
                role.name = name
                self.assertEqual(role.update(['name']).name, name)
