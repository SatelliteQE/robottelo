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
        """Create hosts that can be shared by tests."""
        super(HostCollectionTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.hosts = [
            entities.Host(organization=cls.org).create()
            for _
            in range(2)
        ]

    @tier1
    def test_positive_create_with_name(self):
        """Create host collections with different names.

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
        """Create host collections with different descriptions.

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
        """Create host collections with different limits.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate limit.
        """
        for limit in (1, 3, 5, 10, 20):
            with self.subTest(limit):
                host_collection = entities.HostCollection(
                    max_hosts=limit,
                    organization=self.org,
                ).create()
                self.assertEqual(host_collection.max_hosts, limit)

    @tier1
    def test_positive_create_with_unlimited_hosts(self):
        """Create host collection with different values of 'unlimited hosts'
        parameter.

        @Feature: Host Collection

        @Assert: The host collection was successfully created and has
        appropriate 'unlimited hosts' parameter value.
        """
        for unlimited in (True, False):
            with self.subTest(unlimited):
                host_collection = entities.HostCollection(
                    max_hosts=1 if not unlimited else None,
                    organization=self.org,
                    unlimited_hosts=unlimited,
                ).create()
                self.assertEqual(
                    host_collection.unlimited_hosts, unlimited)

    @skip_if_bug_open('bugzilla', 1325989)
    @tier1
    def test_positive_create_with_host(self):
        """Create a host collection that contains a host.

        @Feature: Host Collection

        @Assert: The host collection can be read back, and it includes one
        host.
        """
        host_collection = entities.HostCollection(
            host=[self.hosts[0]],
            organization=self.org,
        ).create()
        self.assertEqual(len(host_collection.host), 1)

    @skip_if_bug_open('bugzilla', 1325989)
    @tier1
    def test_positive_create_with_hosts(self):
        """Create a host collection that contains hosts.

        @Feature: Host Collection

        @Assert: The host collection can be read back, and it references two
        hosts.
        """
        host_collection = entities.HostCollection(
            host=self.hosts,
            organization=self.org,
        ).create()
        self.assertEqual(len(host_collection.host), len(self.hosts))

    @skip_if_bug_open('bugzilla', 1325989)
    @tier2
    def test_positive_add_host(self):
        """Add a host to host collection.

        @Feature: Host Collection

        @Assert: Host was added to the host collection.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.host = [self.hosts[0]]
        host_collection = host_collection.update(['host'])
        self.assertEqual(len(host_collection.host), 1)

    @skip_if_bug_open('bugzilla', 1325989)
    @tier2
    def test_positive_add_hosts(self):
        """Add hosts to host collection.

        @Feature: Host Collection

        @Assert: Hosts were added to the host collection.
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.host = self.hosts
        host_collection = host_collection.update(['host'])
        self.assertEqual(len(host_collection.host), len(self.hosts))

    @skip_if_bug_open('bugzilla', 1325989)
    @tier1
    def test_positive_read_host_ids(self):
        """Read a host collection and look at the ``host_ids`` field.

        @Feature: Host Collection

        @Assert: The ``host_ids`` field matches the host IDs passed in when
        creating the host collection.
        """
        host_collection = entities.HostCollection(
            host=self.hosts,
            organization=self.org,
        ).create()
        self.assertEqual(
            frozenset((host.id for host in host_collection.host)),
            frozenset((host.id for host in self.hosts)),
        )

    @tier1
    def test_positive_update_name(self):
        """Check if host collection name can be updated

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
        """Check if host collection description can be updated

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
        """Check if host collection limit can be updated

        @Feature: Host Collection

        @Assert: Host collection limit was updated
        """
        host_collection = entities.HostCollection(
            max_hosts=1,
            organization=self.org,
            unlimited_hosts=False,
        ).create()
        for limit in (1, 3, 5, 10, 20):
            with self.subTest(limit):
                host_collection.max_hosts = limit
                self.assertEqual(
                    host_collection.update().max_hosts, limit)

    @tier1
    def test_positive_update_unlimited_hosts(self):
        """Check if host collection 'unlimited hosts' parameter can be updated

        @Feature: Host Collection

        @Assert: Host collection 'unlimited hosts' parameter was updated
        """
        random_unlimited = choice([True, False])
        host_collection = entities.HostCollection(
            max_hosts=1 if not random_unlimited else None,
            organization=self.org,
            unlimited_hosts=random_unlimited,
        ).create()
        for unlimited in (not random_unlimited, random_unlimited):
            with self.subTest(unlimited):
                host_collection.max_hosts = 1 if not unlimited else None
                host_collection.unlimited_hosts = unlimited
                host_collection = host_collection.update(
                    ['max_hosts', 'unlimited_hosts'])
                self.assertEqual(
                    host_collection.unlimited_hosts, unlimited)

    @skip_if_bug_open('bugzilla', 1325989)
    @tier1
    def test_positive_update_host(self):
        """Update host collection's host.

        @Feature: Host Collection

        @Assert: The host collection was updated with a new host.
        """
        host_collection = entities.HostCollection(
            host=[self.hosts[0]],
            organization=self.org,
        ).create()
        host_collection.host = self.hosts[1]
        host_collection = host_collection.update(['host'])
        self.assertEqual(host_collection.host[0].id, self.hosts[1].id)

    @skip_if_bug_open('bugzilla', 1325989)
    @tier1
    def test_positive_update_hosts(self):
        """Update host collection's hosts.

        @Feature: Host Collection

        @Assert: The host collection was updated with new hosts.
        """
        host_collection = entities.HostCollection(
            host=self.hosts,
            organization=self.org,
        ).create()
        new_hosts = [
            entities.Host(organization=self.org).create()
            for _
            in range(2)
        ]
        host_collection.host = new_hosts
        host_collection = host_collection.update(['host'])
        self.assertEqual(
            {host.id for host in host_collection.host},
            {host.id for host in new_hosts}
        )

    @tier1
    def test_positive_delete(self):
        """Check if host collection can be deleted

        @Feature: Host Collection

        @Assert: Host collection was successfully deleted
        """
        host_collection = entities.HostCollection(
            organization=self.org).create()
        host_collection.delete()
        with self.assertRaises(HTTPError):
            host_collection.read()

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create host collections with different invalid names

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
