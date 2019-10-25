# -*- encoding: utf-8 -*-
"""Test class for Operating System CLI

:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from fauxfactory import gen_alphanumeric, gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.defaults import Defaults
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.factory import (
    CLIFactoryError,
    make_architecture,
    make_medium,
    make_os,
    make_partition_table,
    make_template,
)
from robottelo.constants import DEFAULT_ORG
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    destructive,
    tier1,
    tier2,
    upgrade,
)
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

    @tier1
    def test_positive_search_by_name(self):
        """Search for newly created OS by name

        :id: ff9f667c-97ca-49cd-902b-a9b18b5aa021

        :expectedresults: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'name=%s' % os['name']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    @tier1
    def test_positive_search_by_title(self):
        """Search for newly created OS by title

        :id: a555e848-f1f2-4326-aac6-9de8ff45abee

        :expectedresults: Operating System is created and listed

        :CaseImportance: Critical
        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'title=\\"%s\\"' % os['title']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    @tier1
    def test_positive_list(self):
        """Displays list for operating system

        :id: fca309c5-edff-4296-a800-55470669935a

        :expectedresults: Operating System is created and listed

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

    @tier1
    def test_positive_info_by_id(self):
        """Displays info for operating system by its ID

        :id: b8f23b53-439a-4726-9757-164d99d5ed05

        :expectedresults: Operating System is created and can be looked up by
            its ID

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

    @tier1
    def test_positive_create_with_name(self):
        """Create Operating System for all variations of name

        :id: d36eba9b-ccf6-4c9d-a07f-c74eebada89b

        :expectedresults: Operating System is created and can be found

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                self.assertEqual(os['name'], name)

    @tier1
    def test_positive_create_with_arch_medium_ptable(self):
        """Create an OS pointing to an arch, medium and partition table.

        :id: 05bdb2c6-0d2e-4141-9e07-3ada3933b577

        :expectedresults: An operating system is created.

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

    @tier1
    def test_negative_create_with_name(self):
        """Create Operating System using invalid names

        :id: 848a20ce-292a-47d8-beea-da5916c43f11

        :expectedresults: Operating System is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_os({'name': name})

    @tier1
    def test_positive_update_name(self):
        """Positive update of operating system name

        :id: 49b655f7-ba9b-4bb9-b09d-0f7140969a40

        :expectedresults: Operating System name is updated

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

    @tier1
    def test_positive_update_major_version(self):
        """Update an Operating System's major version.

        :id: 38a89dbe-6d1c-4602-a4c1-664425668de8

        :expectedresults: Operating System major version is updated

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

    @tier1
    def test_negative_update_name(self):
        """Negative update of system name

        :id: 4b18ff6d-7728-4245-a1ce-38e62c05f454

        :expectedresults: Operating System name is not updated

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

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Successfully deletes Operating System by its ID

        :id: a67a7b01-081b-42f8-a9ab-1f41166d649e

        :expectedresults: Operating System is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                OperatingSys.delete({'id': os['id']})
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.info({'id': os['id']})

    @tier1
    def test_negative_delete_by_id(self):
        """Delete Operating System using invalid data

        :id: d29a9c95-1fe3-4a7a-9f7b-127be065856d

        :expectedresults: Operating System is not deleted

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

    @tier2
    def test_positive_add_arch(self):
        """Add Architecture to operating system

        :id: 99add22d-d936-4232-9441-beff85867040

        :expectedresults: Architecture is added to Operating System

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

    @tier2
    @upgrade
    def test_positive_add_template(self):
        """Add provisioning template to operating system

        :id: 0ea9eb88-2d27-423d-a9d3-fdd788b4e28a

        :expectedresults: Provisioning template is added to Operating System

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

    @tier2
    def test_positive_add_ptable(self):
        """Add partition table to operating system

        :id: beba676f-b4e4-48e1-bb0c-18ad91847566

        :expectedresults: Partition table is added to Operating System

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

    @tier2
    def test_positive_update_parameters_attributes(self):
        """Update os-parameters-attributes to operating system

        :id: 5d566eea-b323-4128-9356-3bf39943e4d4

        :BZ: 1713553

        :expectedresults: Os-parameters-attributes are updated to Operating System
        """
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        os_id = make_os()['id']
        OperatingSys.update({
            'id': os_id,
            'os-parameters-attributes': 'name={}, value={}'.format(param_name+'\\', param_value),
        })
        os = OperatingSys.info({'id': os_id}, output_format='json')
        self.assertEqual(param_name, os['parameters'][0]['name'])
        self.assertEqual(param_value, os['parameters'][0]['value'])

    @destructive
    @pytest.mark.skip_if_open("BZ:1649011")
    def test_positive_os_list_with_default_organization_set(self):
        """list operating systems when the default organization is set

        :id: 2c1ba416-a5d5-4031-b154-54794569a85b

        :BZ: 1649011

        :expectedresults: os list should list operating systems when the
            default organization is set
        """
        make_os()
        os_list_before_default = OperatingSys.list()
        self.assertTrue(len(os_list_before_default) > 0)
        try:
            Defaults.add({
                u'param-name': 'organization',
                u'param-value': DEFAULT_ORG,
            })
            result = ssh.command('hammer defaults list')
            self.assertEqual(result.return_code, 0)
            self.assertTrue(DEFAULT_ORG in "".join(result.stdout))
            os_list_after_default = OperatingSys.list()
            self.assertTrue(len(os_list_after_default) > 0)

        finally:
            Defaults.delete({u'param-name': 'organization'})
            result = ssh.command('hammer defaults list')
            self.assertEqual(result.return_code, 0)
            self.assertTrue(DEFAULT_ORG not in "".join(result.stdout))
