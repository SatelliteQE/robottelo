"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html

"""
import random
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.common.decorators import data, run_only_on
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
@ddt
class EnvironmentTestCase(APITestCase):
    """Tests for environments."""

    @data(
        gen_string('alpha', random.randint(1, 255)),
        gen_string('numeric', random.randint(1, 255)),
        gen_string('alphanumeric', random.randint(1, 255)),
    )
    def test_positive_create_1(self, name):
        """@Test: Create an environment and provide a valid name.

        @Assert: The environment has the provided attributes.

        @Feature: Environment

        """
        # Create an environment and validate the returned data.
        attrs = entities.Environment(name=name).create_json()
        self.assertEqual(attrs['name'], name)

        # Let's double-check by reading the environment.
        attrs = entities.Environment(id=attrs['id']).read_json()
        self.assertEqual(attrs['name'], name)

    @data(
        gen_string('alpha', 256),
        gen_string('numeric', 256),
        gen_string('alphanumeric', 256),
        gen_string('cjk', random.randint(1, 255)),
        gen_string('latin1', random.randint(1, 255)),
        gen_string('utf8', random.randint(1, 255)),
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
        with self.assertRaises(HTTPError):
            entities.Environment(name=name).create_json()
