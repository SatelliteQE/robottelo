"""Unit tests for the ``ptables`` paths.

A full API reference for patition tables can be found here:
http://theforeman.org/api/apidoc/v2/ptables.html


:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: tstrych

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


class TestPartitionTable:
    """Tests for the ``ptables`` path."""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'name', **parametrized(generate_strings_list(length=1, exclude_types='alphanumeric'))
    )
    def test_positive_create_with_one_character_name(self, target_sat, name):
        """Create Partition table with 1 character in name

        :id: 71601d96-8ce8-4ecb-b053-af6f26a246ea

        :parametrized: yes

        :expectedresults: Partition table was created

        :BZ: 1229384

        :CaseImportance: Low
        """
        ptable = target_sat.api.PartitionTable(name=name).create()
        assert ptable.name == name

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'name, new_name',
        **parametrized(
            list(
                zip(
                    generate_strings_list(length=gen_integer(4, 30)),
                    generate_strings_list(length=gen_integer(4, 30)),
                )
            )
        ),
    )
    def test_positive_crud_with_name(self, target_sat, name, new_name):
        """Create new, search, update and delete partition tables using different inputs as a name

        :id: 32250f23-3704-496f-83e6-6379a415650a

        :parametrized: yes

        :expectedresults: Partition table is created, searched, updated and deleted successfully
            with correct name

        :CaseImportance: Critical
        """
        ptable = target_sat.api.PartitionTable(name=name).create()
        assert ptable.name == name
        result = target_sat.api.PartitionTable().search(query={'search': f'name="{ptable.name}"'})
        assert len(result) == 1
        assert result[0].id == ptable.id
        ptable.name = new_name
        assert ptable.update(['name']).name == new_name
        ptable.delete()
        with pytest.raises(HTTPError):
            ptable.read()

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'layout, new_layout', **parametrized(list(zip(valid_data_list(), valid_data_list())))
    )
    def test_positive_create_update_with_layout(self, target_sat, layout, new_layout):
        """Create new and update partition tables using different inputs as a
            layout

        :id: 5cdf156f-72d9-4950-b11c-4bca5d2aa5bb

        :parametrized: yes

        :expectedresults: Partition table is created and updated successfully and has correct
            layout

        :CaseImportance: Critical
        """
        ptable = target_sat.api.PartitionTable(layout=layout).create()
        assert ptable.layout == layout
        ptable.layout = new_layout
        assert ptable.update(['layout']).layout == new_layout

    @pytest.mark.tier1
    def test_positive_create_with_layout_length(self, target_sat):
        """Create a Partition Table with layout length more than 4096 chars

        :id: 7a07d70c-6130-4357-81c3-4f1254e519d2

        :expectedresults: Partition table created successfully and has correct
            layout

        :BZ: 1270181
        """
        layout = gen_string('alpha', 5000)
        ptable = target_sat.api.PartitionTable(layout=layout).create()
        assert ptable.layout == layout

    @pytest.mark.tier1
    def test_positive_create_update_with_os(self, target_sat):
        """Create new partition table with random operating system and update it with
            random operating system

        :id: 52c6125b-ff50-4a7f-8be0-cb270baf5aa0

        :expectedresults: Partition table created and updated successfully and has correct
            operating system

        """
        os_family = random.choice(OPERATING_SYSTEMS)
        ptable = target_sat.api.PartitionTable(os_family=os_family).create()
        assert ptable.os_family == os_family
        new_os_family = random.choice(OPERATING_SYSTEMS)
        ptable.os_family = new_os_family
        assert ptable.update(['os_family']).os_family == new_os_family

    def test_positive_create_search_with_org(self, target_sat, module_org):
        """Create new partition table with organization and try to find it using its name and
            organization it assigned to

        :id: e6e78c43-8251-4a44-a5c0-4e4d9f71323e

        :expectedresults: Partition table created successfully and has correct
            organization assigned

        :CaseImportance: Medium
        """
        ptable = target_sat.api.PartitionTable(organization=[module_org]).create()
        assert ptable.organization[0].read().name == module_org.name
        result = target_sat.api.PartitionTable().search(
            query={'search': ptable.name, 'organization_id': module_org.id}
        )
        assert len(result) == 1
        assert result[0].read().organization[0].id == module_org.id

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(self, target_sat, name):
        """Try to create partition table using invalid names only

        :id: 02631917-2f7a-4cf7-bb2a-783349a04758

        :parametrized: yes

        :expectedresults: Partition table was not created

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.PartitionTable(name=name).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('layout', **parametrized(('', ' ', None)))
    def test_negative_create_with_empty_layout(self, target_sat, layout):
        """Try to create partition table with empty layout

        :id: 03cb7a35-e4c3-4874-841b-0760c3b8d6af

        :parametrized: yes

        :expectedresults: Partition table was not created
        """
        with pytest.raises(HTTPError):
            target_sat.api.PartitionTable(layout=layout).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, target_sat, new_name):
        """Try to update partition table using invalid names only

        :id: 7e9face8-2c20-450e-890c-6def6de570ca

        :parametrized: yes

        :expectedresults: Partition table was not updated

        :CaseImportance: Medium
        """
        ptable = target_sat.api.PartitionTable().create()
        ptable.name = new_name
        with pytest.raises(HTTPError):
            assert ptable.update(['name']).name != new_name

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_layout', **parametrized(('', ' ', None)))
    def test_negative_update_layout(self, target_sat, new_layout):
        """Try to update partition table with empty layout

        :id: 35c84c8f-b802-4076-89f2-4ec04cf43a31

        :parametrized: yes

        :expectedresults: Partition table was not updated

        :CaseImportance: Medium
        """
        ptable = target_sat.api.PartitionTable().create()
        ptable.layout = new_layout
        with pytest.raises(HTTPError):
            assert ptable.update(['layout']).layout != new_layout
