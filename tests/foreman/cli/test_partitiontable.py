# -*- encoding: utf-8 -*-
"""Test class for Partition table CLI"""
from random import randint
from robottelo.datafactory import generate_strings_list
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_os, make_partition_table
from robottelo.cli.partitiontable import PartitionTable
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.test import CLITestCase


class PartitionTableUpdateCreateTestCase(CLITestCase):
    """Partition Table CLI tests."""

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
                ptable = make_partition_table({'name': name})
                self.assertEqual(ptable['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Partition Tables with different names

        @Assert: Partition Table is created and has correct name

        @Feature: Partition Table
        """
        for name in generate_strings_list(length=randint(4, 30)):
            with self.subTest(name):
                ptable = make_partition_table({'name': name})
                self.assertEqual(ptable['name'], name)

    @tier1
    def test_positive_create_with_content(self):
        """Create a Partition Table with content

        @Feature: Partition Table

        @Assert: Partition Table is created and has correct content
        """
        content = 'Fake ptable'
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        self.assertTrue(content in ptable_content[0])

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create a Partition Table and update its name

        @Feature: Partition Table

        @Assert: Partition Table is created and its name can be updated
        """
        ptable = make_partition_table()
        for new_name in generate_strings_list(length=randint(4, 30)):
            with self.subTest(new_name):
                PartitionTable.update({
                    'id': ptable['id'],
                    'new-name': new_name,
                })
                ptable = PartitionTable.info({'id': ptable['id']})
                self.assertEqual(ptable['name'], new_name)

    @tier1
    def test_positive_delete_by_id(self):
        """Create a Partition Table then delete it by its ID

        @Feature: Partition Table

        @Assert: Partition Table is deleted
        """
        ptable = make_partition_table()
        PartitionTable.delete({'id': ptable['id']})
        with self.assertRaises(CLIReturnCodeError):
            PartitionTable.info({'id': ptable['id']})

    @tier1
    def test_positive_delete_by_name(self):
        """Create a Partition Table then delete it by its name

        @Feature: Partition Table

        @Assert: Partition Table is deleted
        """
        ptable = make_partition_table()
        PartitionTable.delete({'name': ptable['name']})
        with self.assertRaises(CLIReturnCodeError):
            PartitionTable.info({'name': ptable['name']})

    @tier2
    def test_positive_add_os_by_id(self):
        """Create a partition table then add an operating system to it using
        IDs for association

        @Feature: Partition Table

        @Assert: Operating system is added to partition table
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        })
        ptable = PartitionTable.info({'id': ptable['id']})
        self.assertIn(os['title'], ptable['operating-systems'])

    @tier2
    def test_positive_add_os_by_name(self):
        """Create a partition table then add an operating system to it using
        names for association

        @Feature: Partition Table

        @Assert: Operating system is added to partition table
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system({
            'name': ptable['name'],
            'operatingsystem': os['title'],
        })
        ptable = PartitionTable.info({'name': ptable['name']})
        self.assertIn(os['title'], ptable['operating-systems'])

    @tier2
    def test_positive_remove_os_by_id(self):
        """Add an operating system to a partition table then remove it. Use IDs
        for removal

        @Feature: Partition Table

        @Assert: Operating system is added then removed from partition table
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        })
        ptable = PartitionTable.info({'id': ptable['id']})
        PartitionTable.remove_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        })
        ptable = PartitionTable.info({'id': ptable['id']})
        self.assertNotIn(os['title'], ptable['operating-systems'])

    @tier2
    def test_positive_remove_os_by_name(self):
        """Add an operating system to a partition table then remove it. Use
        names for removal

        @Feature: Partition Table

        @Assert: Operating system is added then removed from partition table
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system({
            'name': ptable['name'],
            'operatingsystem': os['title'],
        })
        ptable = PartitionTable.info({'name': ptable['name']})
        PartitionTable.remove_operating_system({
            'name': ptable['name'],
            'operatingsystem': os['title'],
        })
        ptable = PartitionTable.info({'name': ptable['name']})
        self.assertNotIn(os['title'], ptable['operating-systems'])
