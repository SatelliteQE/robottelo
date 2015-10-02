"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html

"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import one_to_many_names
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.helpers import invalid_names_list
from robottelo.test import APITestCase


@run_only_on('sat')
class EnvironmentTestCase(APITestCase):
    """Tests for environments."""

    def test_positive_create_1(self):
        """@Test: Create an environment and provide a valid name.

        @Assert: The environment has the provided attributes.

        @Feature: Environment

        """
        for name in (
                gen_string(str_type)
                for str_type in ('alpha', 'numeric', 'alphanumeric')):
            with self.subTest(name):
                env = entities.Environment(name=name).create()
                self.assertEqual(env.name, name)
                env = env.read()  # check sat isn't blindly handing back data
                self.assertEqual(env.name, name)

    def test_negative_create_1(self):
        """@Test: Create an environment and provide an invalid name.

        @Assert: The server returns an error.

        @Feature: Environment

        In this test, an "invalid name" is one that is too long.

        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Environment(name=name).create()

    def test_negative_create_2(self):
        """@Test: Create an environment and provide an illegal name.

        @Assert: The server returns an error.

        @Feature: Environment

        In this test, an "invalid name" is one that contains illegal
        characters, such as latin1 characters.

        """
        str_types = ('cjk', 'latin1', 'utf8')
        for name in (gen_string(str_type) for str_type in str_types):
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Environment(name=name).create()


@skip_if_bug_open('bugzilla', 1262029)
class MissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.

    """

    @classmethod
    def setUpClass(cls):
        """Create an ``Environment``."""
        super(MissingAttrTestCase, cls).setUpClass()
        env = entities.Environment().create()
        cls.env_attrs = set(env.update_json([]).keys())

    def test_location(self):
        """@Test: Update an environment. Inspect the server's response.

        @Assert: The response contains some value for the ``location`` field.

        @Feature: Environment

        """
        names = one_to_many_names('location')
        self.assertGreater(
            len(names & self.env_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.env_attrs),
        )

    def test_organization(self):
        """@Test: Update an environment. Inspect the server's response.

        @Assert: The response contains some value for the ``organization``
        field.

        @Feature: Environment

        """
        names = one_to_many_names('organization')
        self.assertGreater(
            len(names & self.env_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.env_attrs),
        )
