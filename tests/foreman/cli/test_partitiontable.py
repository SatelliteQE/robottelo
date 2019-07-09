# -*- encoding: utf-8 -*-
"""Test class for Partition table CLI

:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string

from robottelo.datafactory import generate_strings_list
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_os, make_partition_table
from robottelo.cli.partitiontable import PartitionTable
from robottelo.decorators import (
     skip_if_bug_open, tier1, tier2, upgrade)
from robottelo.test import CLITestCase


class PartitionTableUpdateCreateTestCase(CLITestCase):
    """Partition Table CLI tests."""

    @skip_if_bug_open('bugzilla', 1229384)
    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create Partition table with 1 character in name

        :id: cfec857c-ed6e-4472-93bb-70e1d4f39bae

        :expectedresults: Partition table was created

        :BZ: 1229384

        :CaseImportance: Medium
        """
        for name in generate_strings_list(length=1):
            with self.subTest(name):
                ptable = make_partition_table({'name': name})
                self.assertEqual(ptable['name'], name)

    @tier1
    def test_positive_create_with_name(self):
        """Create Partition Tables with different names

        :id: e7d8a444-c69a-4863-a715-83d2dcb3b6ec

        :expectedresults: Partition Table is created and has correct name

        :CaseImportance: Critical
        """
        for name in generate_strings_list(length=randint(4, 30)):
            with self.subTest(name):
                ptable = make_partition_table({'name': name})
                self.assertEqual(ptable['name'], name)

    @tier1
    def test_positive_create_with_content(self):
        """Create a Partition Table with content

        :id: 28bfbd8b-2ada-44d0-89f3-63885cfb3495

        :expectedresults: Partition Table is created and has correct content

        :CaseImportance: Critical
        """
        content = 'Fake ptable'
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        self.assertTrue(content in ptable_content[0])

    @tier1
    @upgrade
    def test_positive_create_with_content_length(self):
        """Create a Partition Table with content length more than 4096 chars

        :id: 59e6f9ef-85c2-4229-8831-00edb41b19f4

        :expectedresults: Partition Table is created and has correct content

        :BZ: 1270181
        """
        content = gen_string('alpha', 5000)
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        self.assertTrue(content in ptable_content[0])

    @tier1
    def test_positive_update_name(self):
        """Create a Partition Table and update its name

        :id: 6242c915-0f15-4d5f-9f7a-73cb58fac81e

        :expectedresults: Partition Table is created and its name can be
            updated

        :CaseImportance: Medium
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

        :id: 4d2369eb-4dc1-4ab5-96d4-c872c39f4ff5

        :expectedresults: Partition Table is deleted

        :CaseImportance: Critical
        """
        ptable = make_partition_table()
        PartitionTable.delete({'id': ptable['id']})
        with self.assertRaises(CLIReturnCodeError):
            PartitionTable.info({'id': ptable['id']})

    @tier1
    @upgrade
    def test_positive_delete_by_name(self):
        """Create a Partition Table then delete it by its name

        :id: 27bd427c-7601-4f3b-998f-b7baaaad0fb0

        :expectedresults: Partition Table is deleted
        """
        ptable = make_partition_table()
        PartitionTable.delete({'name': ptable['name']})
        with self.assertRaises(CLIReturnCodeError):
            PartitionTable.info({'name': ptable['name']})

    @tier2
    def test_positive_add_os_by_id(self):
        """Create a partition table then add an operating system to it using
        IDs for association

        :id: 37415a34-5dba-4551-b1c5-e6e59329f4ca

        :expectedresults: Operating system is added to partition table

        :CaseLevel: Integration
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

        :id: ad97800a-0ef8-4ee9-ab49-05c82c77017f

        :expectedresults: Operating system is added to partition table

        :CaseLevel: Integration
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

        :id: ee37be42-9ed3-44dd-9206-514e340e5524

        :expectedresults: Operating system is added then removed from partition
            table

        :CaseLevel: Integration
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
    @upgrade
    def test_positive_remove_os_by_name(self):
        """Add an operating system to a partition table then remove it. Use
        names for removal

        :id: f7544419-af4c-4dcf-8673-cad472745794

        :expectedresults: Operating system is added then removed from partition
            table

        :CaseLevel: Integration
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
