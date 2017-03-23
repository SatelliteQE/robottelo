# -*- encoding: utf-8 -*-
"""Test class for Operating System CLI

:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.factory import (
    CLIFactoryError,
    make_architecture,
    make_medium,
    make_os,
    make_partition_table,
    make_template,
)
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import CLITestCase


@filtered_datapoint
def negative_delete_data():
    """Returns a list of invalid data for operating system deletion"""
    return [
        {'id': gen_string("alpha")},
        {'id': None},
        {'id': ""},
        {},
        {'id': -1},
    ]


class OperatingSystemTestCase(CLITestCase):
    """Test class for Operating System CLI."""

    @run_only_on('sat')
    @tier1
    def test_positive_search_by_name(self):
        """Search for newly created OS by name

        :id: ff9f667c-97ca-49cd-902b-a9b18b5aa021

        :assert: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'name=%s' % os['name']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    @run_only_on('sat')
    @tier1
    def test_positive_search_by_title(self):
        """Search for newly created OS by title

        :id: a555e848-f1f2-4326-aac6-9de8ff45abee

        :assert: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'title=\\"%s\\"' % os['title']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """Displays list for operating system

        :id: fca309c5-edff-4296-a800-55470669935a

        :assert: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        name = gen_string('alpha')
        os = make_os({'name': name})
        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    @run_only_on('sat')
    @tier1
    def test_positive_info_by_id(self):
        """Displays info for operating system by its ID

        :id: b8f23b53-439a-4726-9757-164d99d5ed05

        :assert: Operating System is created and can be looked up by its ID

        :CaseImportance: Critical
        """
        os = make_os()
        os_info = OperatingSys.info({'id': os['id']})
        # Info does not return major or minor but a concat of name,
        # major and minor
        self.assertEqual(os['id'], os_info['id'])
        self.assertEqual(os['name'], os_info['name'])
        self.assertEqual(str(os['major-version']), os_info['major-version'])
        self.assertEqual(str(os['minor-version']), os_info['minor-version'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Operating System for all variations of name

        :id: d36eba9b-ccf6-4c9d-a07f-c74eebada89b

        :assert: Operating System is created and can be found

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                self.assertEqual(os['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_arch_medium_ptable(self):
        """Create an OS pointing to an arch, medium and partition table.

        :id: 05bdb2c6-0d2e-4141-9e07-3ada3933b577

        :assert: An operating system is created.

        :CaseImportance: Critical
        """
        architecture = make_architecture()
        medium = make_medium()
        ptable = make_partition_table()
        operating_system = make_os({
            u'architecture-ids': architecture['id'],
            u'medium-ids': medium['id'],
            u'partition-table-ids': ptable['id'],
        })

        for attr in (
                'architectures', 'installation-media', 'partition-tables'):
            self.assertEqual(len(operating_system[attr]), 1)
        self.assertEqual(
            operating_system['architectures'][0], architecture['name'])
        self.assertEqual(
            operating_system['installation-media'][0], medium['name'])
        self.assertEqual(
            operating_system['partition-tables'][0], ptable['name'])

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_name(self):
        """Create Operating System using invalid names

        :id: 848a20ce-292a-47d8-beea-da5916c43f11

        :assert: Operating System is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_os({'name': name})

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Positive update of operating system name

        :id: 49b655f7-ba9b-4bb9-b09d-0f7140969a40

        :assert: Operating System name is updated

        :CaseImportance: Critical
        """
        os = make_os({'name': gen_alphanumeric()})
        for new_name in valid_data_list():
            with self.subTest(new_name):
                OperatingSys.update({
                    'id': os['id'],
                    'name': new_name,
                })
                result = OperatingSys.info({'id': os['id']})
                self.assertEqual(result['id'], os['id'], )
                self.assertNotEqual(result['name'], os['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_major_version(self):
        """Update an Operating System's major version.

        :id: 38a89dbe-6d1c-4602-a4c1-664425668de8

        :assert: Operating System major version is updated

        :CaseImportance: Critical
        """
        os = make_os()
        # New value for major
        major = int(os['major-version']) + 1
        OperatingSys.update({
            'id': os['id'],
            'major': major,
        })
        os = OperatingSys.info({
            'id': os['id'],
        })
        self.assertEqual(int(os['major-version']), major)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Negative update of system name

        :id: 4b18ff6d-7728-4245-a1ce-38e62c05f454

        :assert: Operating System name is not updated

        :CaseImportance: Critical
        """
        os = make_os({'name': gen_alphanumeric()})
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.update({
                        'id': os['id'],
                        'name': new_name,
                    })
                result = OperatingSys.info({'id': os['id']})
                self.assertEqual(result['name'], os['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """Successfully deletes Operating System by its ID

        :id: a67a7b01-081b-42f8-a9ab-1f41166d649e

        :assert: Operating System is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                OperatingSys.delete({'id': os['id']})
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.info({'id': os['id']})

    @run_only_on('sat')
    @tier1
    def test_negative_delete_by_id(self):
        """Delete Operating System using invalid data

        :id: d29a9c95-1fe3-4a7a-9f7b-127be065856d

        :assert: Operating System is not deleted

        :CaseImportance: Critical
        """
        for test_data in negative_delete_data():
            with self.subTest(test_data):
                os = make_os()
                # The delete method requires the ID which we will not pass
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.delete(test_data)
                # Now make sure that it still exists
                result = OperatingSys.info({'id': os['id']})
                self.assertEqual(os['id'], result['id'])
                self.assertEqual(os['name'], result['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_add_arch(self):
        """Add Architecture to operating system

        :id: 99add22d-d936-4232-9441-beff85867040

        :assert: Architecture is added to Operating System

        :CaseLevel: Integration
        """
        architecture = make_architecture()
        os = make_os()
        OperatingSys.add_architecture({
            'architecture-id': architecture['id'],
            'id': os['id'],
        })
        os = OperatingSys.info({'id': os['id']})
        self.assertEqual(len(os['architectures']), 1)
        self.assertEqual(architecture['name'], os['architectures'][0])

    @run_only_on('sat')
    @tier2
    def test_positive_add_template(self):
        """Add provisioning template to operating system

        :id: 0ea9eb88-2d27-423d-a9d3-fdd788b4e28a

        :assert: Provisioning template is added to Operating System

        :CaseLevel: Integration
        """
        template = make_template()
        os = make_os()
        OperatingSys.add_config_template({
            'config-template': template['name'],
            'id': os['id'],
        })
        os = OperatingSys.info({'id': os['id']})
        self.assertEqual(len(os['templates']), 1)
        template_name = os['templates'][0]
        self.assertTrue(template_name.startswith(template['name']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_ptable(self):
        """Add partition table to operating system

        :id: beba676f-b4e4-48e1-bb0c-18ad91847566

        :assert: Partition table is added to Operating System

        :CaseLevel: Integration
        """
        # Create a partition table.
        ptable_name = make_partition_table()['name']
        # Create an operating system.
        os_id = make_os()['id']
        # Add the partition table to the operating system.
        OperatingSys.add_ptable({
            'id': os_id,
            'partition-table': ptable_name,
        })
        # Verify that the operating system has a partition table.
        os = OperatingSys.info({'id': os_id})
        self.assertEqual(len(os['partition-tables']), 1)
        self.assertEqual(os['partition-tables'][0], ptable_name)
