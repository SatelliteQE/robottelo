"""Unit tests for host collections."""
from nailgun import entities
from robottelo.common.decorators import skip_if_bug_open
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


class HostCollectionTestCase(APITestCase):
    """Tests for host collections."""

    @classmethod
    def setUpClass(cls):
        """Create systems that can be shared by tests."""
        cls.org_id = entities.Organization().create_json()['id']
        cls.system_uuids = [
            entities.System(organization=cls.org_id).create_json()['id']
            for _
            in range(2)
        ]

    def test_create_with_system(self):
        """@Test: Create a host collection that contains a content host.

        @Feature: HostCollection

        @Assert: The host collection can be read back, and it includes one
        content host.

        """
        hc_id = entities.HostCollection(
            organization=self.org_id,
            system=[self.system_uuids[0]],
        ).create_json()['id']
        self.assertEqual(
            len(entities.HostCollection(id=hc_id).read().system),
            1
        )

    def test_create_with_systems(self):
        """@Test: Create a host collection that contains content hosts.

        @Feature: HostCollection

        @Assert: The host collection can be read back, and it references two
        content hosts.

        """
        hc_id = entities.HostCollection(
            organization=self.org_id,
            system=self.system_uuids,
        ).create_json()['id']
        self.assertEqual(
            len(entities.HostCollection(id=hc_id).read().system),
            len(self.system_uuids),
        )

    @skip_if_bug_open('bugzilla', 1203323)
    def test_read_system_ids(self):
        """@Test: Read a host collection and look at the ``system_ids`` field.

        @Feature: HostCollection

        @Assert: The ``system_ids`` field matches the system IDs passed in when
        creating the host collection.

        """
        hc_id = entities.HostCollection(
            organization=self.org_id,
            system=self.system_uuids,
        ).create_json()['id']
        hc_attrs = entities.HostCollection(id=hc_id).read_json()
        self.assertEqual(
            frozenset(hc_attrs['system_ids']),
            frozenset(self.system_uuids),
        )
