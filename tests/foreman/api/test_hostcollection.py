"""Unit tests for host collections."""
from nailgun import entities
from robottelo.decorators import skip_if_bug_open
from robottelo.test import APITestCase


class HostCollectionTestCase(APITestCase):
    """Tests for host collections."""

    @classmethod
    def setUpClass(cls):
        """Create systems that can be shared by tests."""
        cls.org = entities.Organization().create()
        cls.systems = [
            entities.System(organization=cls.org).create()
            for _
            in range(2)
        ]

    def test_create_with_system(self):
        """@Test: Create a host collection that contains a content host.

        @Feature: HostCollection

        @Assert: The host collection can be read back, and it includes one
        content host.

        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=[self.systems[0]],
        ).create()
        self.assertEqual(len(host_collection.system), 1)

    def test_create_with_systems(self):
        """@Test: Create a host collection that contains content hosts.

        @Feature: HostCollection

        @Assert: The host collection can be read back, and it references two
        content hosts.

        """
        host_collection = entities.HostCollection(
            organization=self.org,
            system=self.systems,
        ).create()
        self.assertEqual(len(host_collection.system), len(self.systems))

    @skip_if_bug_open('bugzilla', 1203323)
    def test_read_system_ids(self):
        """@Test: Read a host collection and look at the ``system_ids`` field.

        @Feature: HostCollection

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
