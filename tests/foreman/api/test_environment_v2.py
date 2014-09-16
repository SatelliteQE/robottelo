"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html

"""
from fauxfactory import FauxFactory
from robottelo.common import decorators
from robottelo.factory import FactoryError
from robottelo import entities
from unittest import TestCase
import ddt
import random
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class EnvironmentTestCase(TestCase):
    """Tests for environments."""
    @decorators.data(
        FauxFactory.generate_string('alpha', random.randint(1, 255)),
        FauxFactory.generate_string('numeric', random.randint(1, 255)),
        FauxFactory.generate_string('alphanumeric', random.randint(1, 255)),
    )
    def test_positive_create_1(self, name):
        """@Test: Create an environment and provide a valid name.

        @Assert: The environment has the provided attributes.

        @Feature: Environment

        """
        # Create an environment and validate the returned data.
        attrs = entities.Environment(name=name).create()
        self.assertEqual(attrs['name'], name)

        # Let's double-check by reading the environment.
        attrs = entities.Environment(id=attrs['id']).read_json()
        self.assertEqual(attrs['name'], name)

    @decorators.data(
        FauxFactory.generate_string('alpha', 256),
        FauxFactory.generate_string('numeric', 256),
        FauxFactory.generate_string('alphanumeric', 256),
        FauxFactory.generate_string('cjk', random.randint(1, 255)),
        FauxFactory.generate_string('latin1', random.randint(1, 255)),
        FauxFactory.generate_string('utf8', random.randint(1, 255)),
    )
    def test_negative_create_1(self, name):
        """@Test: Create an environment and provide an invalid name.

        @Assert: The server returns an error.

        @Feature: Environment

        In the context of this test, an "invalid name" is one that it either
        too long or contains illegal characters. The API returns this error
        message when an illegal character is submitted:

            Name is alphanumeric and cannot contain spaces

        """
        with self.assertRaises(FactoryError):
            entities.Environment(name=name).create()
