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
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase


class ArchitectureTestCase(APITestCase):
    """Tests for architectures."""

    @tier2
    def test_positive_post_hash(self):
        """Do not wrap API calls in an extra hash.

        @id: 44654ec5-5211-4326-bcad-9824f36a036f

        @Assert: It is possible to associate an activation key with an
        organization.

        @CaseLevel: Integration
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

        @id: 9943063d-34f3-4dbc-a341-474ec781e4d9

        @Assert: The architecture can be created, and the association can be
        read back from the server.

        @CaseLevel: Integration
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

        @id: acbadcda-3410-45cb-a3aa-932a0facadc1

        @Assert: Architecture is created and contains provided name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                self.assertEqual(name, arch.name)

    @tier1
    @skip_if_bug_open('bugzilla', 1401519)
    def test_negative_create_with_invalid_name(self):
        """Create architecture providing an invalid initial name.
        set.

        @id: c740b8c4-8ee3-4481-b041-4eff2faf9055

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

        @id: 8dbbf4f8-188e-406a-9099-a707f553d6bb

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

        @id: 301b335e-9bc1-47d9-8bef-a8ca2e9ea18e

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

        @id: 114a2973-a889-4a5e-bfac-de4406826258

        @Assert: architecture is successfully deleted.
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                arch.delete()
                with self.assertRaises(HTTPError):
                    entities.Architecture(id=arch.id).read()
