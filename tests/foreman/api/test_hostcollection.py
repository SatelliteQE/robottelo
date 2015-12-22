"""Unit tests for host collections."""
from nailgun import entities
from random import choice
from requests.exceptions import HTTPError
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.test import APITestCase


class HostCollectionTestCase(APITestCase):
    """Tests for host collections."""

    @classmethod
    def setUpClass(cls):
        """Create content hosts that can be shared by tests."""
        super(HostCollectionTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.systems = [
            entities.System(organization=cls.org).create()
            for _
            in range(2)
        ]

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create host collections with different names.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                host_collection = entities.HostCollection(
                    name=name,
                    organization=self.org,
                ).create()
                self.assertEqual(host_collection.name, name)

    @tier1
    def test_positive_create_with_description(self):
        """@Test: Create host collections with different descriptions.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate description.
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                host_collection = entities.HostCollection(
                    description=desc,
                    organization=self.org,
                ).create()
                self.assertEqual(host_collection.description, desc)

    @tier1
    def test_positive_create_with_limit(self):
        """@Test: Create host collections with different limits.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate limit.
        """
        for limit in (1, 3, 5, 10, 20):
            with self.subTest(limit):
                host_collection = entities.HostCollection(
                    max_content_hosts=limit,
                    organization=self.org,
                ).create()
                self.assertEqual(host_collection.max_content_hosts, limit)

    @tier1
    def test_positive_create_with_unlimited_chosts(self):
        """@Test: Create host collection with different values of 'unlimited
        content hosts' parameter.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate 'unlimited content hosts' parameter value.
        """
        for unlimited in (True, False):
            with self.subTest(unlimited):
                host_collection = entities.HostCollection(
                    organization=self.org,
                    unlimited_content_hosts=unlimited,
                ).create()
                self.assertEqual(
                    host_collection.unlimited_content_hosts, unlimited)

    @tier1
    def test_positive_create_with_chost(self):
        """@Test: Create a host collection that contains a content host.

        @Feature: Host Collection

        @Assert: The host collection can be read back, and it includes one
        content host.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=[self.systems[0]],
        ).create()
        self.assertEqual(len(host_collection.system), 1)

    @tier1
    def test_positive_create_with_chosts(self):
        """@Test: Create a host collection that contains content hosts.

        @Feature: Host Collection

        @Assert: The host collection can be read back, and it references two
        content hosts.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=self.systems,
        ).create()
        self.assertEqual(len(host_collection.system), len(self.systems))

    @tier2
    def test_positive_add_chost(self):
        """@Test: Add content host to host collection.

        @Feature: Host Collection

        @Assert: Content host was added to the host collection.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.system = [self.systems[0]]
        host_collection = host_collection.update(['system'])
        self.assertEqual(len(host_collection.system), 1)

    @tier2
    def test_positive_add_chosts(self):
        """@Test: Add content hosts to host collection.

        @Feature: Host Collection

        @Assert: Content hosts were added to the host collection.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.system = self.systems
        host_collection = host_collection.update(['system'])
        self.assertEqual(len(host_collection.system), len(self.systems))

    @tier1
    @skip_if_bug_open('bugzilla', 1203323)
    def test_positive_read_system_ids(self):
        """@Test: Read a host collection and look at the ``system_ids`` field.

        @Feature: Host Collection

        @Assert: The ``system_ids`` field matches the system IDs passed in when
        creating the host collection.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=self.systems,
        ).create()
        self.assertEqual(
            frozenset((system.id for system in host_collection.system)),
            frozenset((system.id for system in self.systems)),
        )

    @tier1
    def test_positive_update_name(self):
        """@Test: Check if host collection name can be updated

        @Feature: Host Collection

        @Assert: Host collection name was successfully updated
        """
        host_collection = entities.HostCollection(
            organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                host_collection.name = new_name
                self.assertEqual(host_collection.update().name, new_name)

    @tier1
    def test_positive_update_description(self):
        """@Test: Check if host collection description can be updated

        @Feature: Host Collection

        @Assert: Host collection description was updated
        """
        host_collection = entities.HostCollection(
            organization=self.org).create()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                host_collection.description = new_desc
                self.assertEqual(
                    host_collection.update().description, new_desc)

    @tier1
    def test_positive_update_limit(self):
        """@Test: Check if host collection limit can be updated

        @Feature: Host Collection

        @Assert: Host collection limit was updated
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            unlimited_content_hosts=False,
        ).create()
        for limit in (1, 3, 5, 10, 20):
            with self.subTest(limit):
                host_collection.max_content_hosts = limit
                self.assertEqual(
                    host_collection.update().max_content_hosts, limit)

    @tier1
    def test_positive_update_unlimited_chosts(self):
        """@Test: Check if host collection 'unlimited content hosts' parameter
        can be updated

        @Feature: Host Collection

        @Assert: Host collection 'unlimited content hosts' parameter was
        updated
        """
        random_unlimited = choice([True, False])
        host_collection = entities.HostCollection(
            organization=self.org,
            unlimited_content_hosts=random_unlimited,
        ).create()
        for unlimited in (not random_unlimited, random_unlimited):
            with self.subTest(unlimited):
                host_collection.unlimited_content_hosts = unlimited
                host_collection = host_collection.update(
                    ['unlimited_content_hosts'])
                self.assertEqual(
                    host_collection.unlimited_content_hosts, unlimited)

    @tier1
    @skip_if_bug_open('bugzilla', 1203323)
    def test_positive_update_chost(self):
        """@Test: Update host collection's content host.

        @Feature: Host Collection

        @Assert: The host collection was updated with new content host.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=[self.systems[0]],
        ).create()
        host_collection.system = self.systems[1]
        host_collection = host_collection.update(['system'])
        self.assertEqual(host_collection.system[0].id, self.systems[1].id)

    @tier1
    @skip_if_bug_open('bugzilla', 1203323)
    def test_positive_update_chosts(self):
        """@Test: Update host collection's content hosts.

        @Feature: Host Collection

        @Assert: The host collection was updated with new content hosts.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=self.systems,
        ).create()
        new_systems = [
            entities.System(organization=self.org).create()
            for _
            in range(2)
        ]
        host_collection.system = new_systems
        host_collection = host_collection.update(['system'])
        self.assertEqual(
            {system.id for system in host_collection.system},
            {system.id for system in new_systems}
        )

    @tier1
    def test_positive_delete(self):
        """@Test: Check if host collection can be deleted

        @Feature: Host Collection

        @Assert: Host collection was successfully deleted
        """
        host_collection = entities.HostCollection(
            organization=self.org,
            unlimited_content_hosts=False,
        ).create()
        host_collection.delete()
        with self.assertRaises(HTTPError):
            host_collection.read()

    @tier1
    def test_negative_create_with_invalid_name(self):
        """@Test: Try to create host collections with different invalid names

        @Feature: Host Collection

        @Assert: The host collection was not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.HostCollection(
                        name=name,
                        organization=self.org,
                    ).create()
