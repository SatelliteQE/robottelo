# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition table CLI
"""
from robottelo.test import CLITestCase
from robottelo.common.helpers import generate_name
from robottelo.cli.factory import make_partition_table
from robottelo.cli.partitiontable import PartitionTable
from robottelo.common import ssh
import tempfile


class TestPartitionTableUpdateCreate(CLITestCase):
    """Test case for CLI tests."""

    def setUp(self):
        """Set up file"""
        super(TestPartitionTableUpdateCreate, self).setUp()
        self.file = tempfile.NamedTemporaryFile(delete=True)
        self.file.write("This is a test partition table file")
        self.content = "Fake ptable"
        self.name = generate_name(6)
        ssh.upload_file(self.file.name, remote_file=self.file.name)

    def tearDown(self):
        """Remove the file"""
        self.file.close()

    def test_create_ptable(self):
        """
        @Feature: Partition Table - Create
        @Test: Check if Partition Table can be created
        @Assert: Partition Table is created
        """

        args = {
            'name': self.name,
            'os-family': 'Redhat',
            'file': self.file.name,
            'content': self.content
        }
        try:
            make_partition_table(args)
        except Exception as e:
                self.fail(e)
        result = PartitionTable().exists(tuple_search=('name', self.name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

    def test_update_ptable(self):
        """
        @Feature: Partition Table - Update
        @Test: Check if Partition Table can be updated
        @Assert: Partition Table is updated
        """

        args = {
            'name': self.name,
            'os-family': 'Redhat',
            'file': self.file.name,
            'content': self.content
        }
        try:
            make_partition_table(args)
        except Exception as e:
                self.fail(e)
        result = PartitionTable().exists(tuple_search=('name', self.name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        new_name = generate_name(6)
        self.args = {
            'name': self.name,
            'os-family': 'Redhat',
            'file': self.file.name,
            'new-name': new_name
        }

        result = PartitionTable().update(self.args)
        self.assertEqual(result.return_code, 0, "Failed to update object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(tuple_search=('new-name',
                                                  new_name)).stdout)


class TestPartitionTableDelete(CLITestCase):
    """Test case for Dump/Delete CLI tests."""

    def test_dump_ptable_1(self):
        """
        @Feature: Partition Table - Create
        @Test: Check if Partition Table can be created with specific content
        @Assert: Partition Table is created
        """

        content = "Fake ptable"
        name = generate_name(6)
        make_partition_table({'name': name, 'content': content})

        ptable = PartitionTable().exists(tuple_search=('name', name)).stdout

        args = {
            'id': ptable['id'],
        }

        ptable_content = PartitionTable().dump(args)

        self.assertTrue(content in ptable_content.stdout[0])

    def test_delete_ptable_1(self):
        """
        @Feature: Partition Table - Delete
        @Test: Check if Partition Table can be deleted
        @Assert: Partition Table is deleted
        """

        content = "Fake ptable"
        name = generate_name(6)
        make_partition_table({'name': name, 'content': content})

        ptable = PartitionTable().exists(tuple_search=('name', name)).stdout

        args = {
            'id': ptable['id'],
        }

        result = PartitionTable().delete(args)
        self.assertEqual(result.return_code, 0, "Deletion Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(tuple_search=('name', name)).stdout)
