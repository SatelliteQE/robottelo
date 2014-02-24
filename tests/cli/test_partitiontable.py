# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition table CLI
"""

from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.factory import make_partition_table
from robottelo.common.helpers import generate_name
from tests.cli.basecli import MetaCLI


class TestPartitionTable(MetaCLI):

    factory = make_partition_table
    factory_obj = PartitionTable

    def test_dump_ptable_1(self):
        """
        @Feature: Partition Table - Create
        @Test: Check if Partition Table can be created with specific content
        @Assert: Partition Table is created
        """

        content = "Fake ptable"
        name = generate_name(6)
        make_partition_table({'name': name, 'content': content})

        ptable = PartitionTable().exists(('name', name)).stdout

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

        ptable = PartitionTable().exists(('name', name)).stdout

        args = {
            'id': ptable['id'],
        }

        PartitionTable().delete(args)
        self.assertFalse(PartitionTable().exists(('name', name)).stdout)
