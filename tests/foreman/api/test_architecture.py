"""Unit tests for the ``architectures`` paths.

@Requirement: Architecture
@CaseAutomation: Automated
@CaseLevel: Acceptance
@CaseComponent: API
@TestType: Functional
@CaseImportance: High
@Upstream: No
"""


from fauxfactory import gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import tier1, tier2
from robottelo.test import APITestCase


class ArchitectureTestCase(APITestCase):
    """Tests for architectures."""

    @tier2
    def test_positive_post_hash(self):
        """Do not wrap API calls in an extra hash.

        @ID: 20540385-dad4-44d9-85d0-3157cf641aa2

        @Assert: It is possible to associate an activation key with an
        organization.

        @Level: Integration
        """
        name = gen_string('utf8')
        os = entities.OperatingSystem().create()
        response = client.post(
            entities.Architecture().path(),
            {u'name': name, u'operatingsystem_ids': [os.id]},
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        attrs = response.json()

        # The server will accept some POSTed attributes (name) and silently
        # ignore others (operatingsystem_ids).
        self.assertIn('name', attrs)
        self.assertEqual(name, attrs['name'])
        self.assertIn('operatingsystems', attrs)
        self.assertEqual(os.id, attrs['operatingsystems'][0]['id'])

    @tier2
    def test_positive_add_os(self):
        """Create an architecture and associate it with an OS.

        @ID: 1091f1a2-2969-4afa-8cc6-d868f3e49980

        @Assert: The architecture can be created, and the association can be
        read back from the server.

        @Level: Integration
        """
        operating_sys = entities.OperatingSystem().create()
        arch = entities.Architecture(operatingsystem=[operating_sys]).create()
        self.assertEqual(
            {operating_sys.id},
            {os.id for os in arch.operatingsystem},
        )

    @tier1
    def test_positive_create_with_name(self):
        """Create an architecture providing the initial name.

        @ID: a008fc85-72fe-40ba-a29c-fb25e6a55f98

        @Assert: Architecture is created and contains provided name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                self.assertEqual(name, arch.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create architecture providing an invalid initial name.
        set.

        @ID: a868465b-0175-4a0e-a927-2e98bf498a2d

        @Assert: Architecture is not created
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Architecture(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """Create architecture then update its name to another
        valid name.

        @ID: 47118177-36c5-4644-bebd-b9b1642a1d90

        @Assert: Architecture is created, and its name can be updated.
        """
        arch = entities.Architecture().create()

        for new_name in valid_data_list():
            with self.subTest(new_name):
                entities.Architecture(
                    id=arch.id, name=new_name).update(['name'])
                updated = entities.Architecture(id=arch.id).read()
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_name(self):
        """Create architecture then update its name to an invalid name.

        @ID: 96e2d4d6-6341-4c6a-88e9-cfd84d2d8b47

        @Assert: Architecture is created, and its name is not updated.
        """
        arch = entities.Architecture().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Architecture(
                        id=arch.id, name=new_name).update(['name'])
                arch = entities.Architecture(id=arch.id).read()
                self.assertNotEqual(arch.name, new_name)

    @tier1
    def test_positive_delete(self):
        """Create architecture and then delete it.

        @ID: 9f34c3ea-c2ba-4cee-ac10-bd8699c7865b

        @Assert: architecture is successfully deleted.
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                arch.delete()
                with self.assertRaises(HTTPError):
                    entities.Architecture(id=arch.id).read()
