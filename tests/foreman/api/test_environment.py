"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html

"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import one_to_many_names
from robottelo.datafactory import datacheck, invalid_names_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase


@datacheck
def valid_data_list():
    """Return a list of various kinds of valid strings for Environment entity
    """
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


class EnvironmentTestCase(APITestCase):
    """Tests for environments."""

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create an environment and provide a valid name.

        @Feature: Environment

        @Assert: The environment created successfully and has expected name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                env = entities.Environment(name=name).create()
                self.assertEqual(env.name, name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_org(self):
        """Create an environment and assign it to new organization.

        @Feature: Environment

        @Assert: The environment created successfully and has expected
        attributes.
        """
        org = entities.Organization().create()
        env = entities.Environment(
            name=gen_string('alphanumeric'),
            organization=[org],
        ).create()
        self.assertEqual(len(env.organization), 1)
        self.assertEqual(env.organization[0].id, org.id)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_loc(self):
        """Create an environment and assign it to new location.

        @Feature: Environment

        @Assert: The environment created successfully and has expected
        attributes.
        """
        location = entities.Location().create()
        env = entities.Environment(
            name=gen_string('alphanumeric'),
            location=[location],
        ).create()
        self.assertEqual(len(env.location), 1)
        self.assertEqual(env.location[0].id, location.id)

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_too_long_name(self):
        """Create an environment and provide an invalid name.

        @Feature: Environment

        @Assert: The server returns an error.
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Environment(name=name).create()

    @tier2
    @run_only_on('sat')
    def test_negative_create_with_invalid_characters(self):
        """Create an environment and provide an illegal name.

        @Feature: Environment

        @Assert: The server returns an error.
        """
        str_types = ('cjk', 'latin1', 'utf8')
        for name in (gen_string(str_type) for str_type in str_types):
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Environment(name=name).create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Create environment entity providing the initial name, then
        update its name to another valid name.

        @Feature: Environment

        @Assert: Environment entity is created and updated properly
        """
        env = entities.Environment().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                env = entities.Environment(
                    id=env.id, name=new_name).update(['name'])
                self.assertEqual(env.name, new_name)

    @tier2
    @run_only_on('sat')
    def test_positive_update_org(self):
        """Update environment and assign it to a new organization

        @Feature: Environment

        @Assert: Environment entity is updated properly
        """
        env = entities.Environment().create()
        org = entities.Organization().create()
        env = entities.Environment(
            id=env.id, organization=[org]).update(['organization'])
        self.assertEqual(len(env.organization), 1)
        self.assertEqual(env.organization[0].id, org.id)

    @tier2
    @run_only_on('sat')
    def test_positive_update_loc(self):
        """Update environment and assign it to a new location

        @Feature: Environment

        @Assert: Environment entity is updated properly
        """
        env = entities.Environment().create()
        location = entities.Location().create()
        env = entities.Environment(
            id=env.id, location=[location]).update(['location'])
        self.assertEqual(len(env.location), 1)
        self.assertEqual(env.location[0].id, location.id)

    @tier1
    @run_only_on('sat')
    def test_negative_update_name(self):
        """Create environment entity providing the initial name, then
        try to update its name to invalid one.

        @Feature: Environment

        @Assert: Environment entity is not updated
        """
        env = entities.Environment().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Environment(
                        id=env.id, name=new_name).update(['name'])

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create new environment entity and then delete it.

        @Feature: Environment

        @Assert: Environment entity is deleted successfully
        """
        for name in valid_data_list():
            with self.subTest(name):
                env = entities.Environment(name=name).create()
                env.delete()
                with self.assertRaises(HTTPError):
                    env.read()


@skip_if_bug_open('bugzilla', 1262029)
class MissingAttrEnvironmentTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.

    """

    @classmethod
    def setUpClass(cls):
        """Create an ``Environment``."""
        super(MissingAttrEnvironmentTestCase, cls).setUpClass()
        env = entities.Environment().create()
        cls.env_attrs = set(env.update_json([]).keys())

    @tier2
    def test_location(self):
        """Update an environment. Inspect the server's response.

        @Assert: The response contains some value for the ``location`` field.

        @Feature: Environment
        """
        names = one_to_many_names('location')
        self.assertGreater(
            len(names & self.env_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.env_attrs),
        )

    @tier2
    def test_organization(self):
        """Update an environment. Inspect the server's response.

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
