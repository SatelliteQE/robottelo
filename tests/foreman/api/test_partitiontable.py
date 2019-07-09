"""Unit tests for the ``ptables`` paths.

A full API reference for patition tables can be found here:
http://theforeman.org/api/apidoc/v2/ptables.html


:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer, gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import APITestCase


class PartitionTableTestCase(APITestCase):
    """Tests for the ``ptables`` path."""

    @skip_if_bug_open('bugzilla', 1229384)
    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create Partition table with 1 character in name

        :id: 71601d96-8ce8-4ecb-b053-af6f26a246ea

        :expectedresults: Partition table was created

        :BZ: 1229384

        :CaseImportance: Low
        """
        for name in generate_strings_list(length=1):
            with self.subTest(name):
                ptable = entities.PartitionTable(name=name).create()
                self.assertEqual(ptable.name, name)

    @tier1
    def test_positive_create_with_name(self):
        """Create new partition tables using different inputs as a name

        :id: f774051a-8ad4-48dc-b652-0e3c382b6043

        :expectedresults: Partition table created successfully and has correct
            name

        :CaseImportance: Critical
        """
        for name in generate_strings_list(length=gen_integer(4, 30)):
            with self.subTest(name):
                ptable = entities.PartitionTable(name=name).create()
                self.assertEqual(ptable.name, name)

    @tier1
    def test_positive_create_with_layout(self):
        """Create new partition tables using different inputs as a
        layout

        :id: 12e9d821-415e-4e8b-b4c6-9921c74c1fc5

        :expectedresults: Partition table created successfully and has correct
            layout

        :CaseImportance: Critical
        """
        for layout in valid_data_list():
            with self.subTest(layout):
                ptable = entities.PartitionTable(layout=layout).create()
                self.assertEqual(ptable.layout, layout)

    @tier1
    def test_positive_create_with_layout_length(self):
        """Create a Partition Table with layout length more than 4096 chars

        :id: 7a07d70c-6130-4357-81c3-4f1254e519d2

        :expectedresults: Partition table created successfully and has correct
            layout

        :BZ: 1270181
        """
        layout = gen_string('alpha', 5000)
        ptable = entities.PartitionTable(layout=layout).create()
        self.assertEqual(ptable.layout, layout)

    @tier1
    def test_positive_create_with_os(self):
        """Create new partition table with random operating system

        :id: ebd55ed6-5fb2-4f17-ac73-b56661ee5254

        :expectedresults: Partition table created successfully and has correct
            operating system

        """
        os_family = OPERATING_SYSTEMS[randint(0, 8)]
        ptable = entities.PartitionTable(os_family=os_family).create()
        self.assertEqual(ptable.os_family, os_family)

    def test_positive_create_with_org(self):
        """Create new partition table with organization

        :id: 5f97b180-3708-4e1c-8407-42977459d4b6

        :expectedresults: Partition table created successfully and has correct
            organization assigned

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        ptable = entities.PartitionTable(organization=[org]).create()
        self.assertEqual(ptable.organization[0].read().name, org.name)

    def test_positive_search(self):
        """Create new partition table and try to find it using its name

        :id: 08520746-444b-47c9-a8a3-438170147453

        :expectedresults: Search functionality works as expected and correct
            partition table returned
        """
        ptable = entities.PartitionTable().create()
        result = entities.PartitionTable().search(
            query={'search': ptable.name})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, ptable.id)

    @skip_if_bug_open('bugzilla', 1375788)
    def test_positive_search_by_organization(self):
        """Create new partition table and try to find it using its name and
        organization it assigned to

        :id: cdbc5d5a-c924-4cb3-8b54-d84fc6bbb651

        :expectedresults: Search functionality works as expected and correct
            partition table returned

        :BZ: 1375788

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        ptable = entities.PartitionTable(organization=[org]).create()
        result = entities.PartitionTable().search(query={
            'search': ptable.name, 'organization_id': org.id
        })
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].read().organization[0].id, org.id)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create partition table using invalid names only

        :id: 02631917-2f7a-4cf7-bb2a-783349a04758

        :expectedresults: Partition table was not created

        :CaseImportance: Medium
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.PartitionTable(name=name).create()

    @tier1
    def test_negative_create_with_empty_layout(self):
        """Try to create partition table with empty layout

        :id: 03cb7a35-e4c3-4874-841b-0760c3b8d6af

        :expectedresults: Partition table was not created
        """
        for layout in ('', ' ', None):
            with self.subTest(layout):
                with self.assertRaises(HTTPError):
                    entities.PartitionTable(layout=layout).create()

    @tier1
    def test_positive_delete(self):
        """Delete partition table

        :id: 36133202-8849-432e-838b-3d13d088ef28

        :expectedresults: Partition table was deleted

        :CaseImportance: Critical
        """
        ptable = entities.PartitionTable().create()
        ptable.delete()
        with self.assertRaises(HTTPError):
            ptable.read()

    @tier1
    def test_positive_update_name(self):
        """Update partition tables with new name

        :id: 8bde5a54-21a8-420e-b6cb-1d81c381d0b2

        :expectedresults: Partition table updated successfully and name was
            changed

        :CaseImportance: Medium
        """
        ptable = entities.PartitionTable().create()
        for new_name in generate_strings_list(length=gen_integer(4, 30)):
            with self.subTest(new_name):
                ptable.name = new_name
                self.assertEqual(ptable.update(['name']).name, new_name)

    @tier1
    def test_positive_update_layout(self):
        """Update partition table with new layout

        :id: 329eea6e-3474-4cc1-87d4-15e765e0a255

        :expectedresults: Partition table updated successfully and layout was
            changed
        """
        ptable = entities.PartitionTable().create()
        for new_layout in valid_data_list():
            with self.subTest(new_layout):
                ptable.layout = new_layout
                self.assertEqual(ptable.update(['layout']).layout, new_layout)

    @tier1
    def test_positive_update_os(self):
        """Update partition table with new random operating system

        :id: bf03d80c-3527-4b0a-b6c7-4629a8eaefb2

        :expectedresults: Partition table updated successfully and operating
            system was changed
        """
        ptable = entities.PartitionTable(
            os_family=OPERATING_SYSTEMS[0],
        ).create()
        new_os_family = OPERATING_SYSTEMS[randint(1, 8)]
        ptable.os_family = new_os_family
        self.assertEqual(ptable.update(['os_family']).os_family, new_os_family)

    @tier1
    def test_negative_update_name(self):
        """Try to update partition table using invalid names only

        :id: 7e9face8-2c20-450e-890c-6def6de570ca

        :expectedresults: Partition table was not updated

        :CaseImportance: Medium
        """
        ptable = entities.PartitionTable().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                ptable.name = new_name
                with self.assertRaises(HTTPError):
                    self.assertNotEqual(ptable.update(['name']).name, new_name)

    @tier1
    def test_negative_update_layout(self):
        """Try to update partition table with empty layout

        :id: 35c84c8f-b802-4076-89f2-4ec04cf43a31

        :expectedresults: Partition table was not updated

        :CaseImportance: Medium
        """
        ptable = entities.PartitionTable().create()
        for new_layout in ('', ' ', None):
            with self.subTest(new_layout):
                ptable.layout = new_layout
                with self.assertRaises(HTTPError):
                    self.assertNotEqual(
                        ptable.update(['layout']).layout,
                        new_layout
                    )
