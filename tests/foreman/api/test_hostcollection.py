"""Unit tests for host collections.

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: HostCollections

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
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

        :id: 8f2b9223-f5be-4cb1-8316-01ea747cae14

        :expectedresults: The host collection was successfully created and has
            appropriate name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                host_collection = entities.HostCollection(
                    name=name,
                    organization=self.org,
                ).create()
                self.assertEqual(host_collection.name, name)

    @tier1
    def test_positive_list(self):
        """Create new host collection and then retrieve list of all existing
        host collections

        :id: 6ae32df2-b917-4830-8709-15fb272b76c1

        :BZ: 1331875

        :expectedresults: Returned list of host collections for the system
            contains at least one collection

        :CaseImportance: Critical
        """
        entities.HostCollection(organization=self.org).create()
        hc_list = entities.HostCollection().search()
        self.assertGreaterEqual(len(hc_list), 1)

    @tier1
    def test_positive_list_for_organization(self):
        """Create host collection for specific organization. Retrieve list of
        host collections for that organization

        :id: 5f9de8ab-2c53-401b-add3-57d86c97563a

        :expectedresults: The host collection was successfully created and
            present in the list of collections for specific organization

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        hc = entities.HostCollection(organization=org).create()
        hc_list = entities.HostCollection(organization=org).search()
        self.assertEqual(len(hc_list), 1)
        self.assertEqual(hc_list[0].id, hc.id)

    @tier1
    def test_positive_create_with_description(self):
        """Create host collections with different descriptions.

        :id: 9d13392f-8d9d-4ff1-8909-4233e4691055

        :expectedresults: The host collection was successfully created and has
            appropriate description.

        :CaseImportance: Critical
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

        :id: 86d9387b-7036-4794-96fd-5a3472dd9160

        :expectedresults: The host collection was successfully created and has
            appropriate limit.

        :CaseImportance: Critical
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

        :id: d385574e-5794-4442-b6cd-e5ded001d877

        :expectedresults: The host collection was successfully created and has
            appropriate 'unlimited hosts' parameter value.

        :CaseImportance: Critical
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

    @tier1
    def test_positive_create_with_host(self):
        """Create a host collection that contains a host.

        :id: 9dc0ad72-58c2-4079-b1ca-2c4373472f0f

        :expectedresults: The host collection can be read back, and it includes
            one host.

        :CaseImportance: Critical

        :BZ: 1325989
        """
        host_collection = entities.HostCollection(
            host=[self.hosts[0]],
            organization=self.org,
        ).create()
        self.assertEqual(len(host_collection.host), 1)

    @tier1
    def test_positive_create_with_hosts(self):
        """Create a host collection that contains hosts.

        :id: bb8d2b42-9a8b-4c4f-ba0c-c56ae5a7eb1d

        :expectedresults: The host collection can be read back, and it
            references two hosts.

        :CaseImportance: Critical

        :BZ: 1325989
        """
        host_collection = entities.HostCollection(
            host=self.hosts,
            organization=self.org,
        ).create()
        self.assertEqual(len(host_collection.host), len(self.hosts))

    @tier2
    def test_positive_add_host(self):
        """Add a host to host collection.

        :id: da8bc901-7ac8-4029-bb62-af21aa4d3a88

        :expectedresults: Host was added to the host collection.

        :CaseLevel: Integration

        :BZ:1325989
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.host = [self.hosts[0]]
        host_collection = host_collection.update(['host'])
        self.assertEqual(len(host_collection.host), 1)

    @upgrade
    @tier2
    def test_positive_add_hosts(self):
        """Add hosts to host collection.

        :id: f76b4db1-ccd5-47ab-be15-8c7d91d03b22

        :expectedresults: Hosts were added to the host collection.

        :CaseLevel: Integration

        :BZ: 1325989
        """
        host_collection = entities.HostCollection(
            organization=self.org,
        ).create()
        host_collection.host = self.hosts
        host_collection = host_collection.update(['host'])
        self.assertEqual(len(host_collection.host), len(self.hosts))

    @tier1
    def test_positive_read_host_ids(self):
        """Read a host collection and look at the ``host_ids`` field.

        :id: 444a1528-64c8-41b6-ba2b-6c49799d5980

        :expectedresults: The ``host_ids`` field matches the host IDs passed in
            when creating the host collection.

        :CaseImportance: Critical

        :BZ:1325989
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

        :id: b2dedb99-6dd7-41be-8aaa-74065c820ac6

        :expectedresults: Host collection name was successfully updated

        :CaseImportance: Critical
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

        :id: f8e9bd1c-1525-4b5f-a07c-eb6b6e7aa628

        :expectedresults: Host collection description was updated

        :CaseImportance: Critical
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

        :id: 4eda7796-cd81-453b-9b72-4ef84b2c1d8c

        :expectedresults: Host collection limit was updated

        :CaseImportance: Critical
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

        :id: 09a3973d-9832-4255-87bf-f9eaeab4aee8

        :expectedresults: Host collection 'unlimited hosts' parameter was
            updated

        :CaseImportance: Critical
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

    @tier1
    def test_positive_update_host(self):
        """Update host collection's host.

        :id: 23082854-abcf-4085-be9c-a5d155446acb

        :expectedresults: The host collection was updated with a new host.

        :CaseImportance: Critical
        """
        host_collection = entities.HostCollection(
            host=[self.hosts[0]],
            organization=self.org,
        ).create()
        host_collection.host = [self.hosts[1]]
        host_collection = host_collection.update(['host'])
        self.assertEqual(host_collection.host[0].id, self.hosts[1].id)

    @upgrade
    @tier1
    def test_positive_update_hosts(self):
        """Update host collection's hosts.

        :id: 0433b37d-ae16-456f-a51d-c7b800334861

        :expectedresults: The host collection was updated with new hosts.

        :CaseImportance: Critical
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

    @upgrade
    @tier1
    def test_positive_delete(self):
        """Check if host collection can be deleted

        :id: 13a16cd2-16ce-4966-8c03-5d821edf963b

        :expectedresults: Host collection was successfully deleted

        :CaseImportance: Critical
        """
        host_collection = entities.HostCollection(
            organization=self.org).create()
        host_collection.delete()
        with self.assertRaises(HTTPError):
            host_collection.read()

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create host collections with different invalid names

        :id: 38f67d04-a19d-4eab-a577-21b8d62c7389

        :expectedresults: The host collection was not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.HostCollection(
                        name=name,
                        organization=self.org,
                    ).create()

    @tier1
    @stubbed()
    def test_positive_add_subscription(self):
        """Try to add a subscription to a host collection

        :id: c4ec5727-eb25-452e-a91f-87cafb16666b

        :steps:

            1. Create a new or use an existing subscription
            2. Add the subscription to the host collection

        :expectedresults: The subscription was added to the host collection

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_remove_subscription(self):
        """Try to remove a subscription from a host collection

        :id: fdf43e57-5101-4270-9750-afe26f77c53c

        :steps:

            1. Create a new or use an existing subscription
            2. Add the subscription to the host collection
            3. Remove the subscription from the host collection

        :expectedresults: The subscription was added to the host collection

        :CaseImportance: Critical
        """
