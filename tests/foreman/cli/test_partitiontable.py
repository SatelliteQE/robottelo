"""Test class for Partition table CLI

:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: tstrych

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_partition_table
from robottelo.cli.partitiontable import PartitionTable
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import parametrized


class TestPartitionTable:
    """Partition Table CLI tests."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(generate_strings_list(length=1)))
    def test_positive_create_with_one_character_name(self, name):
        """Create Partition table with 1 character in name

        :id: cfec857c-ed6e-4472-93bb-70e1d4f39bae

        :parametrized: yes

        :expectedresults: Partition table was created

        :BZ: 1229384

        :CaseImportance: Medium
        """
        ptable = make_partition_table({'name': name})
        assert ptable['name'] == name

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'name, new_name',
        **parametrized(
            list(
                zip(
                    generate_strings_list(length=randint(4, 30)),
                    generate_strings_list(length=randint(4, 30)),
                )
            )
        )
    )
    def test_positive_crud_with_name(self, name, new_name):
        """Create, read, update and delete Partition Tables with different names

        :id: ce512fef-fbf2-4365-b70b-d30221111d96

        :expectedresults: Partition Table is created, updated and deleted with correct name

        :parametrized: yes

        :CaseImportance: Critical
        """
        ptable = make_partition_table({'name': name})
        assert ptable['name'] == name
        PartitionTable.update({'id': ptable['id'], 'new-name': new_name})
        ptable = PartitionTable.info({'id': ptable['id']})
        assert ptable['name'] == new_name
        PartitionTable.delete({'name': ptable['name']})
        with pytest.raises(CLIReturnCodeError):
            PartitionTable.info({'name': ptable['name']})

    @pytest.mark.tier1
    def test_positive_create_with_content(self):
        """Create a Partition Table with content

        :id: 28bfbd8b-2ada-44d0-89f3-63885cfb3495

        :expectedresults: Partition Table is created and has correct content

        :CaseImportance: Critical
        """
        content = 'Fake ptable'
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        assert content in ptable_content[0]

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_create_with_content_length(self):
        """Create a Partition Table with content length more than 4096 chars

        :id: 59e6f9ef-85c2-4229-8831-00edb41b19f4

        :expectedresults: Partition Table is created and has correct content

        :BZ: 1270181
        """
        content = gen_string('alpha', 5000)
        ptable = make_partition_table({'content': content})
        ptable_content = PartitionTable().dump({'id': ptable['id']})
        assert content in ptable_content[0]

    @pytest.mark.tier1
    def test_positive_delete_by_id(self):
        """Create a Partition Table then delete it by its ID

        :id: 4d2369eb-4dc1-4ab5-96d4-c872c39f4ff5

        :expectedresults: Partition Table is deleted

        :CaseImportance: Critical
        """
        ptable = make_partition_table()
        PartitionTable.delete({'id': ptable['id']})
        with pytest.raises(CLIReturnCodeError):
            PartitionTable.info({'id': ptable['id']})

    @pytest.mark.tier2
    def test_positive_add_remove_os_by_id(self):
        """Create a partition table then add and remove an operating system to it using
        IDs for association

        :id: 33b5ddca-2151-45cb-bf30-951c2733165f

        :expectedresults: Operating system is added to partition table

        :CaseLevel: Integration
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system({'id': ptable['id'], 'operatingsystem-id': os['id']})
        ptable = PartitionTable.info({'id': ptable['id']})
        assert os['title'] in ptable['operating-systems']
        PartitionTable.remove_operating_system({'id': ptable['id'], 'operatingsystem-id': os['id']})
        ptable = PartitionTable.info({'id': ptable['id']})
        assert os['title'] not in ptable['operating-systems']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_remove_os_by_name(self):
        """Create a partition table then add and remove an operating system to it using
        names for association

        :id: 99185fce-fb26-4019-845c-3e5db9afd714

        :expectedresults: Operating system is added to partition table

        :CaseLevel: Integration
        """
        ptable = make_partition_table()
        os = make_os()
        PartitionTable.add_operating_system(
            {'name': ptable['name'], 'operatingsystem': os['title']}
        )
        ptable = PartitionTable.info({'name': ptable['name']})
        assert os['title'] in ptable['operating-systems']
        PartitionTable.remove_operating_system(
            {'name': ptable['name'], 'operatingsystem': os['title']}
        )
        ptable = PartitionTable.info({'name': ptable['name']})
        assert os['title'] not in ptable['operating-systems']
