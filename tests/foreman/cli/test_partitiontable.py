"""Test class for Partition table CLI

:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Endeavour

:CaseImportance: High

"""

from random import randint

from fauxfactory import gen_string
import pytest

from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import generate_strings_list, parametrized


class TestPartitionTable:
    """Partition Table CLI tests."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(generate_strings_list(length=1)))
    def test_positive_create_with_one_character_name(self, name, target_sat):
        """Create Partition table with 1 character in name

        :id: cfec857c-ed6e-4472-93bb-70e1d4f39bae

        :parametrized: yes

        :expectedresults: Partition table was created

        :BZ: 1229384

        :CaseImportance: Medium
        """
        ptable = target_sat.cli_factory.make_partition_table({'name': name})
        assert ptable['name'] == name

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        ('name', 'new_name'),
        **parametrized(
            list(
                zip(
                    generate_strings_list(length=randint(4, 30)),
                    generate_strings_list(length=randint(4, 30)),
                    strict=True,
                )
            )
        ),
    )
    def test_positive_crud_with_name(self, name, new_name, module_target_sat):
        """Create, read, update and delete Partition Tables with different names

        :id: ce512fef-fbf2-4365-b70b-d30221111d96

        :expectedresults: Partition Table is created, updated and deleted with correct name

        :parametrized: yes

        :CaseImportance: Critical
        """
        ptable = module_target_sat.cli_factory.make_partition_table({'name': name})
        assert ptable['name'] == name
        module_target_sat.cli.PartitionTable.update({'id': ptable['id'], 'new-name': new_name})
        ptable = module_target_sat.cli.PartitionTable.info({'id': ptable['id']})
        assert ptable['name'] == new_name
        module_target_sat.cli.PartitionTable.delete({'name': ptable['name']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.PartitionTable.info({'name': ptable['name']})

    @pytest.mark.tier1
    def test_positive_create_with_content(self, module_target_sat):
        """Create a Partition Table with content

        :id: 28bfbd8b-2ada-44d0-89f3-63885cfb3495

        :expectedresults: Partition Table is created and has correct content

        :CaseImportance: Critical
        """
        content = 'Fake ptable'
        filename = gen_string('alpha', 10)
        module_target_sat.execute(f'echo {content} > {filename}')
        ptable = module_target_sat.cli_factory.make_partition_table({'file': filename})
        ptable_content = module_target_sat.cli.PartitionTable().dump({'id': ptable['id']})
        assert content in ptable_content

    @pytest.mark.tier1
    def test_positive_delete_by_id(self, module_target_sat):
        """Create a Partition Table then delete it by its ID

        :id: 4d2369eb-4dc1-4ab5-96d4-c872c39f4ff5

        :expectedresults: Partition Table is deleted

        :CaseImportance: Critical
        """
        ptable = module_target_sat.cli_factory.make_partition_table()
        module_target_sat.cli.PartitionTable.delete({'id': ptable['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.PartitionTable.info({'id': ptable['id']})

    @pytest.mark.tier2
    def test_positive_add_remove_os_by_id(self, module_target_sat):
        """Create a partition table then add and remove an operating system to it using
        IDs for association

        :id: 33b5ddca-2151-45cb-bf30-951c2733165f

        :expectedresults: Operating system is added to partition table

        """
        ptable = module_target_sat.cli_factory.make_partition_table()
        os = module_target_sat.cli_factory.make_os()
        module_target_sat.cli.PartitionTable.add_operating_system(
            {'id': ptable['id'], 'operatingsystem-id': os['id']}
        )
        ptable = module_target_sat.cli.PartitionTable.info({'id': ptable['id']})
        assert os['title'] in ptable['operating-systems']
        module_target_sat.cli.PartitionTable.remove_operating_system(
            {'id': ptable['id'], 'operatingsystem-id': os['id']}
        )
        ptable = module_target_sat.cli.PartitionTable.info({'id': ptable['id']})
        assert os['title'] not in ptable['operating-systems']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_remove_os_by_name(self, module_target_sat):
        """Create a partition table then add and remove an operating system to it using
        names for association

        :id: 99185fce-fb26-4019-845c-3e5db9afd714

        :expectedresults: Operating system is added to partition table

        """
        ptable = module_target_sat.cli_factory.make_partition_table()
        os = module_target_sat.cli_factory.make_os()
        module_target_sat.cli.PartitionTable.add_operating_system(
            {'name': ptable['name'], 'operatingsystem': os['title']}
        )
        ptable = module_target_sat.cli.PartitionTable.info({'name': ptable['name']})
        assert os['title'] in ptable['operating-systems']
        module_target_sat.cli.PartitionTable.remove_operating_system(
            {'name': ptable['name'], 'operatingsystem': os['title']}
        )
        ptable = module_target_sat.cli.PartitionTable.info({'name': ptable['name']})
        assert os['title'] not in ptable['operating-systems']
