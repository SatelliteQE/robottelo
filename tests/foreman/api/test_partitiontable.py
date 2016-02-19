"""Unit tests for the ``ptables`` paths.

A full API reference for patition tables can be found here:
http://theforeman.org/api/apidoc/v2/ptables.html

"""
from fauxfactory import gen_integer
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import APITestCase


class PartitionTableTestCase(APITestCase):
    """Tests for the ``ptables`` path."""

    @skip_if_bug_open('bugzilla', 1229384)
    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create Partition table with 1 character in name

        @Assert: Partition table was created

        @Feature: Partition Table - Create

        @BZ: 1229384
        """
        for name in generate_strings_list(length=1):
            with self.subTest(name):
                ptable = entities.PartitionTable(name=name).create()
                self.assertEqual(ptable.name, name)

    @tier1
    def test_positive_create_with_name(self):
        """Create new partition tables using different inputs as a name

        @Assert: Partition table created successfully and has correct name

        @Feature: Partition Table - Create
        """
        for name in generate_strings_list(length=gen_integer(4, 30)):
            with self.subTest(name):
                ptable = entities.PartitionTable(name=name).create()
                self.assertEqual(ptable.name, name)

    @tier1
    def test_positive_create_with_layout(self):
        """Create new partition tables using different inputs as a
        layout

        @Assert: Partition table created successfully and has correct layout

        @Feature: Partition Table - Create
        """
        for layout in valid_data_list():
            with self.subTest(layout):
                ptable = entities.PartitionTable(layout=layout).create()
                self.assertEqual(ptable.layout, layout)

    @tier1
    def test_positive_create_with_os(self):
        """Create new partition table with random operating system

        @Assert: Partition table created successfully and has correct operating
        system

        @Feature: Partition Table - Create
        """
        os_family = OPERATING_SYSTEMS[randint(0, 8)]
        ptable = entities.PartitionTable(os_family=os_family).create()
        self.assertEqual(ptable.os_family, os_family)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create partition table using invalid names only

        @Assert: Partition table was not created

        @Feature: Partition Table - Create
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.PartitionTable(name=name).create()

    @tier1
    def test_negative_create_with_empty_layout(self):
        """Try to create partition table with empty layout

        @Assert: Partition table was not created

        @Feature: Partition Table - Create
        """
        for layout in ('', ' ', None):
            with self.subTest(layout):
                with self.assertRaises(HTTPError):
                    entities.PartitionTable(layout=layout).create()

    @tier1
    def test_positive_delete(self):
        """Delete partition table

        @Assert: Partition table was deleted

        @Feature: Partition Table - Delete
        """
        ptable = entities.PartitionTable().create()
        ptable.delete()
        with self.assertRaises(HTTPError):
            ptable.read()

    @tier1
    def test_positive_update_name(self):
        """Update partition tables with new name

        @Assert: Partition table updated successfully and name was changed

        @Feature: Partition Table - Update
        """
        ptable = entities.PartitionTable().create()
        for new_name in generate_strings_list(length=gen_integer(4, 30)):
            with self.subTest(new_name):
                ptable.name = new_name
                self.assertEqual(ptable.update(['name']).name, new_name)

    @tier1
    def test_positive_update_layout(self):
        """Update partition table with new layout

        @Assert: Partition table updated successfully and layout was changed

        @Feature: Partition Table - Update
        """
        ptable = entities.PartitionTable().create()
        for new_layout in valid_data_list():
            with self.subTest(new_layout):
                ptable.layout = new_layout
                self.assertEqual(ptable.update(['layout']).layout, new_layout)

    @tier1
    def test_positive_update_os(self):
        """Update partition table with new random operating system

        @Assert: Partition table updated successfully and operating system was
        changed

        @Feature: Partition Table - Update
        """
        ptable = entities.PartitionTable(
            os_family=OPERATING_SYSTEMS[0],
        ).create()
        new_os_family = OPERATING_SYSTEMS[randint(1, 8)]
        ptable.os_family = new_os_family
        self.assertEqual(ptable.update(['os_family']).os_family, new_os_family)

    @tier1
    def test_negative_update_name(self):
        """Try to update partition table using invalid names only

        @Assert: Partition table was not updated

        @Feature: Partition Table - Update
        """
        ptable = entities.PartitionTable().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                ptable.name = new_name
                with self.assertRaises(HTTPError):
                    self.assertNotEqual(ptable.update(['name']).name, new_name)

    @tier1
    def test_negative_update_layout(self):
        """Try to update partition table with empty layout

        @Assert: Partition table was not updated

        @Feature: Partition Table - Update
        """
        ptable = entities.PartitionTable().create()
        for new_layout in ('', ' ', None):
            with self.subTest(new_layout):
                ptable.layout = new_layout
                with self.assertRaises(HTTPError):
                    self.assertNotEqual(
                        ptable.update(['layout']).layout,
                        new_layout
                    )
