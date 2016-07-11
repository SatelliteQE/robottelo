"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html


@Requirement: Environment

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import one_to_many_names
from robottelo.datafactory import filtered_datapoint, invalid_names_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase


@filtered_datapoint
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

        @id: 8869ccf8-a511-4fa7-ac36-11494e85f532

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

        @id: de7e4132-5ca7-4b41-9af3-df075d31f8f4

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

        @id: 34d4bf4a-f36e-4433-999c-beda6916e781

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

        @id: e2654954-b3a1-4594-a487-bcd0cc8195ad

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

        @id: 8ec57d04-4ce6-48b4-b7f9-79025019ad0f

        @Assert: The server returns an error.

        @CaseLevel: Integration
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

        @id: ef48e79a-6b6a-4811-b49b-09f2effdd18f

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

        @id: 31e43faa-65ee-4757-ac3d-3825eba37ae5

        @Assert: Environment entity is updated properly

        @CaseLevel: Integration
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

        @id: da56b040-69e3-4d4f-8ab3-3bfe923eaffe

        @Assert: Environment entity is updated properly

        @CaseLevel: Integration
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

        @id: 9cd024ab-db3d-4b15-b6da-dd2089321df3

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

        @id: 500539c0-f839-4c6b-838f-a3a256962d65

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

        @id: a4c1bc22-d586-4150-92fc-7797f0f5bfb0

        @Assert: The response contains some value for the ``location`` field.

        @CaseLevel: Integration
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

        @id: ac46bcac-5db0-4899-b2fc-d48d2116287e

        @Assert: The response contains some value for the ``organization``
        field.

        @CaseLevel: Integration
        """
        names = one_to_many_names('organization')
        self.assertGreater(
            len(names & self.env_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.env_attrs),
        )
