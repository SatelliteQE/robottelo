# -*- encoding: utf-8 -*-
"""Test class for Partition table CLI"""
from fauxfactory import gen_string, gen_alphanumeric
from robottelo.cli.factory import make_os, make_partition_table
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.partitiontable import PartitionTable
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import CLITestCase


class PartitionTableUpdateCreateTestCase(CLITestCase):
    """Test case for CLI tests."""

    def setUp(self):  # noqa
        """Set up file"""
        super(PartitionTableUpdateCreateTestCase, self).setUp()
        self.content = "Fake ptable"
        self.name = gen_alphanumeric(6)
        self.args = {'name': self.name,
                     'content': self.content}

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name_content(self):
        """@Test: Create a Partition Table with name and content

        @Assert: Partition Table is created and has correct name and content

        @Feature: Partition Table
        """
        ptable = make_partition_table(self.args)
        self.assertEqual(ptable['name'], self.name)

    @tier1
    def test_positive_create_with_content(self):
        """@Test: Create a Partition Table with content

        @Feature: Partition Table

        @Assert: Partition Table is created and has correct content
        """
        content = "Fake ptable"
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        self.assertTrue(content in ptable_content[0])

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """@Test: Create a Partition Table and update its name

        @Feature: Partition Table

        @Assert: Partition Table is created and its name can be updated
        """
        ptable = make_partition_table(self.args)
        self.assertEqual(ptable['name'], self.name)
        new_name = gen_alphanumeric(6)
        PartitionTable().update({
            'name': self.name,
            'new-name': new_name,
        })
        PartitionTable().exists(search=('name', new_name))


class PartitionTableDeleteTestCase(CLITestCase):
    """Test case for Dump/Delete CLI tests."""

    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Create a Partition Table then delete it by its ID

        @Feature: Partition Table

        @Assert: Partition Table is deleted
        """
        content = "Fake ptable"
        name = gen_alphanumeric(6)
        ptable = make_partition_table({'name': name, 'content': content})
        PartitionTable().delete({'id': ptable['id']})
        self.assertFalse(PartitionTable().exists(search=('name', name)))

    # pylint: disable=no-self-use
    @tier2
    def test_positive_add_os_by_id(self):
        """@Test: Create a partition table then add an operating system to it

        @Feature: Partition Table

        @Assert: Operating system is added to partition table

        """
        content = "Fake ptable"
        ptable = make_partition_table({'content': content})
        os_list = OperatingSys.list()
        PartitionTable().add_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os_list[0]['id']
        })

    @tier2
    def test_positive_remove_os_by_id(self):
        """@Test: Add an operating system to a partition table then remove it

        @Feature: Partition Table

        @Assert: Operating system is added then removed from partition table
        """
        ptable = make_partition_table({'content': gen_string("alpha", 10)})
        os = make_os()
        PartitionTable.add_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        })
        ptable = PartitionTable.info({'id': ptable['id']})
        self.assertIn(os['title'], ptable['operating-systems'])
        PartitionTable.remove_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        })
        ptable = PartitionTable.info({'id': ptable['id']})
        self.assertNotIn(os['title'], ptable['operating-systems'])
