# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition table CLI
"""
from robottelo.test import CLITestCase
from robottelo.common.helpers import generate_name
from robottelo.cli.factory import make_partition_table
from robottelo.cli.operatingsys import OperatingSys
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
        self.args = {'name': self.name,
                     'os-family': 'Redhat',
                     'file': self.file.name,
                     'content': self.content}
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

        try:
            make_partition_table(self.args)
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

        try:
            make_partition_table(self.args)
        except Exception as e:
            self.fail(e)
        result = PartitionTable().exists(tuple_search=('name', self.name))
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")

        nw_nm = generate_name(6)
        args = {'name': self.name,
                'os-family': 'Redhat',
                'file': self.file.name,
                'new-name': nw_nm}
        result = PartitionTable().update(args)
        self.assertEqual(result.return_code, 0, "Failed to update object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(tuple_search=('new-name', nw_nm)).stdout)


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

        args = {'id': ptable['id']}

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

        args = {'id': ptable['id']}

        result = PartitionTable().delete(args)
        self.assertEqual(result.return_code, 0, "Deletion Failed")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertFalse(
            PartitionTable().exists(tuple_search=('name', name)).stdout)

    def test_addoperatingsystem_ptable(self):
        """
        @Feature: Partition Table - Add operating system
        @Test: Check if Partition Table can be associated with operating system
        @Assert: Operating system added
        """

        content = "Fake ptable"
        name = generate_name(6)
        try:
            make_partition_table({'name': name, 'content': content})
        except Exception as e:
            self.fail(e)
        result = PartitionTable().exists(tuple_search=('name', name))
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
