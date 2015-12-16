"""Unit tests for the ``architectures`` paths."""
from fauxfactory import gen_utf8
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase


class ArchitectureTestCase(APITestCase):
    """Tests for architectures."""

    @tier2
    @skip_if_bug_open('bugzilla', 1151220)
    def test_positive_post_hash(self):
        """@Test: Do not wrap API calls in an extra hash.

        @Assert: It is possible to associate an activation key with an
        organization.

        @Feature: Architecture
        """
        name = gen_utf8()
        os_id = entities.OperatingSystem().create_json()['id']
        response = client.post(
            entities.Architecture().path(),
            {u'name': name, u'operatingsystem_ids': [os_id]},
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
        self.assertEqual([os_id], attrs['operatingsystems'])

    @tier2
    def test_positive_add_os(self):
        """@Test: Create an architecture and associate it with an OS.

        @Assert: The architecture can be created, and the association can be
        read back from the server.

        @Feature: Architecture
        """
        operating_sys = entities.OperatingSystem().create()
        arch = entities.Architecture(operatingsystem=[operating_sys]).create()
        self.assertEqual(
            {operating_sys.id},
            {os.id for os in arch.operatingsystem},
        )

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create an architecture providing the initial name.

        @Assert: Architecture is created and contains provided name.

        @Feature: Architecture
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                self.assertEqual(name, arch.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """@Test: Create architecture providing an invalid initial name.
        set.

        @Assert: Architecture is not created

        @Feature: Architecture
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Architecture(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """@Test: Create architecture then update its name to another
        valid name.

        @Assert: Architecture is created, and its name can be updated.

        @Feature: Architecture
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
        """@Test: Create architecture then update its name to an invalid name.

        @Assert: Architecture is created, and its name is not updated.

        @Feature: Architecture
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
        """@Test: Create architecture and then delete it.

        @Assert: architecture is successfully deleted.

        @Feature: Architecture
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                arch.delete()
                with self.assertRaises(HTTPError):
                    entities.Architecture(id=arch.id).read()
