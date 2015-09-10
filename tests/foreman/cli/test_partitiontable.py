# -*- encoding: utf-8 -*-
"""Test class for Partition table CLI"""
from fauxfactory import gen_string, gen_alphanumeric
from robottelo.cli.factory import (
    CLIFactoryError, make_partition_table, make_os)
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

        try:
            make_partition_table(self.args)
        except CLIFactoryError as err:
            self.fail(err)
        result = PartitionTable().exists(search=('name', self.name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

    def test_update_ptable(self):
        """@Test: Check if Partition Table can be updated

        @Feature: Partition Table - Update

        @Assert: Partition Table is updated

        """

        try:
            make_partition_table(self.args)
        except CLIFactoryError as err:
            self.fail(err)
        result = PartitionTable().exists(search=('name', self.name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        nw_nm = gen_alphanumeric(6)
        args = {'name': self.name,
                'new-name': nw_nm}
        result = PartitionTable().update(args)
        self.assertEqual(result.return_code, 0, "Failed to update object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(search=('new-name', nw_nm)).stdout)


class TestPartitionTableDelete(CLITestCase):
    """Test case for Dump/Delete CLI tests."""

    def test_dump_ptable_1(self):
        """@Test: Check if Partition Table can be created with specific content

        @Feature: Partition Table - Create

        @Assert: Partition Table is created

        """

        content = "Fake ptable"
        name = gen_alphanumeric(6)
        make_partition_table({'name': name, 'content': content})

        ptable = PartitionTable().exists(search=('name', name)).stdout

        args = {'id': ptable['id']}

        ptable_content = PartitionTable().dump(args)

        self.assertTrue(content in ptable_content.stdout[0])

    def test_delete_ptable_1(self):
        """@Test: Check if Partition Table can be deleted

        @Feature: Partition Table - Delete

        @Assert: Partition Table is deleted

        """

        content = "Fake ptable"
        name = gen_alphanumeric(6)
        make_partition_table({'name': name, 'content': content})

        ptable = PartitionTable().exists(search=('name', name)).stdout

        args = {'id': ptable['id']}

        result = PartitionTable().delete(args)
        self.assertEqual(result.return_code, 0, "Deletion Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(search=('name', name)).stdout)

    def test_addoperatingsystem_ptable(self):
        """@Test: Check if Partition Table can be associated
                  with operating system

        @Feature: Partition Table - Add operating system

        @Assert: Operating system added

        """

        content = "Fake ptable"
        name = gen_alphanumeric(6)
        try:
            make_partition_table({'name': name, 'content': content})
        except CLIFactoryError as err:
            self.fail(err)
        result = PartitionTable().exists(search=('name', name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        ptable = result.stdout

        os_list = OperatingSys.list()
        self.assertEqual(os_list.return_code, 0, "Failed to list os")
        self.assertEqual(
            len(os_list.stderr), 0, "Should not have gotten an error")

        args = {'id': ptable['id'],
                'operatingsystem-id': os_list.stdout[0]['id']}

        result = PartitionTable().add_operating_system(args)
        self.assertEqual(result.return_code, 0, "Association Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

    def test_removeoperatingsystem_ptable(self):
        """@Test: Check if associated operating system can be removed

        @Feature: Partition Table - Add operating system

        @Assert: Operating system removed

        """
        content = gen_string("alpha", 10)
        name = gen_string("alpha", 10)
        try:
            ptable = make_partition_table({'name': name, 'content': content})
            os = make_os()
        except CLIFactoryError as err:
            self.fail(err)

        args = {
            'id': ptable['id'],
            'operatingsystem-id': os['id'],
        }

        result = PartitionTable.add_operating_system(args)
        self.assertEqual(result.return_code, 0, "Association Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        result = PartitionTable.info({'id': ptable['id']})
        self.assertIn(os['title'],
                      result.stdout['operating-systems'])

        result = PartitionTable.remove_operating_system(args)
        self.assertEqual(result.return_code, 0, "Association Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        result = PartitionTable.info({'id': ptable['id']})
        self.assertNotIn(
            os['title'],
            result.stdout['operating-systems'])
