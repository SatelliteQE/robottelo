# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Partition table CLI"""
from fauxfactory import gen_string, gen_alphanumeric
from robottelo.cli.factory import make_os, make_partition_table
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.partitiontable import PartitionTable
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestPartitionTableUpdateCreate(CLITestCase):
    """Test case for CLI tests."""

    def setUp(self):  # noqa
        """Set up file"""
        super(TestPartitionTableUpdateCreate, self).setUp()
        self.content = "Fake ptable"
        self.name = gen_alphanumeric(6)
        self.args = {'name': self.name,
                     'content': self.content}

    def test_create_ptable(self):
        """@Test: Check if Partition Table can be created

        @Assert: Partition Table is created

        @Feature: Partition Table - Create

        """
        ptable = make_partition_table(self.args)
        self.assertEqual(ptable['name'], self.name)

    def test_update_ptable(self):
        """@Test: Check if Partition Table can be updated

        @Feature: Partition Table - Update

        @Assert: Partition Table is updated

        """
        ptable = make_partition_table(self.args)
        self.assertEqual(ptable['name'], self.name)
        new_name = gen_alphanumeric(6)
        PartitionTable().update({
            'name': self.name,
            'new-name': new_name,
        })
        PartitionTable().exists(search=('name', new_name))


class TestPartitionTableDelete(CLITestCase):
    """Test case for Dump/Delete CLI tests."""

    def test_dump_ptable_1(self):
        """@Test: Check if Partition Table can be created with specific content

        @Feature: Partition Table - Create

        @Assert: Partition Table is created

        """
        content = "Fake ptable"
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        self.assertTrue(content in ptable_content[0])

    def test_delete_ptable_1(self):
        """@Test: Check if Partition Table can be deleted

        @Feature: Partition Table - Delete

        @Assert: Partition Table is deleted

        """
        content = "Fake ptable"
        name = gen_alphanumeric(6)
        ptable = make_partition_table({'name': name, 'content': content})
        PartitionTable().delete({'id': ptable['id']})
        self.assertFalse(PartitionTable().exists(search=('name', name)))

    # pylint: disable=no-self-use
    def test_addoperatingsystem_ptable(self):
        """@Test: Check if Partition Table can be associated
                  with operating system

        @Feature: Partition Table - Add operating system

        @Assert: Operating system added

        """
        content = "Fake ptable"
        ptable = make_partition_table({'content': content})
        os_list = OperatingSys.list()
        PartitionTable().add_operating_system({
            'id': ptable['id'],
            'operatingsystem-id': os_list[0]['id']
        })

    def test_remove_os_ptable(self):
        """@Test: Check if associated operating system can be removed

        @Feature: Partition Table - Add operating system

        @Assert: Operating system removed

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
