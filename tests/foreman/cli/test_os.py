# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Operating System CLI"""

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
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.helpers import valid_data_list, invalid_values_list
from robottelo.test import CLITestCase

NEGATIVE_DELETE_DATA = (
    {'id': gen_string("alpha")},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)


@run_only_on('sat')
class TestOperatingSystem(CLITestCase):
    """Test class for Operating System CLI."""

    # Issues
    @skip_if_bug_open('redmine', 4547)
    def test_redmine_4547(self):
        """@test: Search for newly created OS by name

        @feature: Operating System - Search

        @assert: Operating System is created and listed

        @bz: redmine#4547

        """
        os_list_before = OperatingSys.list()
        os = make_os()
        os_list = OperatingSys.list({'search': 'name=%s' % os['name']})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    def test_bugzilla_1051557(self):
        """@test: Update an Operating System's major version.

        @feature: Operating System - Update

        @assert: Operating System major version is updated

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

    def test_bugzilla_1203457(self):
        """@test: Create an OS pointing to an arch, medium and partition table.

        @feature: Operating System - Create

        @assert: An operating system is created.

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

    def test_list_1(self):
        """@test: Displays list for operating system

        @feature: Operating System - List

        @assert: Operating System is created and listed

        """
        os_list_before = OperatingSys.list()
        name = gen_string('alpha')
        os = make_os({'name': name})
        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list[0]['id']})
        self.assertEqual(os['id'], os_info['id'])
        os_list_after = OperatingSys.list()
        self.assertGreater(len(os_list_after), len(os_list_before))

    def test_info_1(self):
        """@test: Displays info for operating system

        @feature: Operating System - Info

        @assert: Operating System is created and have the correct data

        """
        os = make_os()
        os_info = OperatingSys.info({'id': os['id']})
        # Info does not return major or minor but a concat of name,
        # major and minor
        self.assertEqual(os['id'], os_info['id'])
        self.assertEqual(os['name'], os_info['name'])
        self.assertEqual(str(os['major-version']), os_info['major-version'])
        self.assertEqual(str(os['minor-version']), os_info['minor-version'])

    def test_positive_create_1(self):
        """@test: Create Operating System for all variations of name

        @feature: Operating System - Positive Create

        @assert: Operating System is created and can be found

        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                self.assertEqual(os['name'], name)

    def test_negative_create_1(self):
        """@test: Create Operating System using invalid names

        @feature: Operating System - Negative Create

        @assert: Operating System is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_os({'name': name})

    def test_positive_update_1(self):
        """@test: Positive update of system name

        @feature: Operating System - Positive Update

        @assert: Operating System is updated and can be found

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

    def test_negative_update_1(self):
        """@test: Negative update of system name

        @feature: Operating System - Negative Update

        @assert: Operating System is not updated

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

    def test_positive_delete_1(self):
        """@test: Successfully deletes Operating System

        @feature: Operating System - Positive Delete

        @assert: Operating System is deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                os = make_os({'name': name})
                OperatingSys.delete({'id': os['id']})
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.info({'id': os['id']})

    def test_negative_delete_1(self):
        """@test: Not delete Operating System for invalid data

        @feature: Operating System - Negative Delete

        @assert: Operating System is not deleted

        """
        for test_data in NEGATIVE_DELETE_DATA:
            with self.subTest(test_data):
                os = make_os()
                # The delete method requires the ID which we will not pass
                with self.assertRaises(CLIReturnCodeError):
                    OperatingSys.delete(test_data)
                # Now make sure that it still exists
                result = OperatingSys.info({'id': os['id']})
                self.assertEqual(os['id'], result['id'])
                self.assertEqual(os['name'], result['name'])

    def test_add_architecture(self):
        """@test: Add Architecture to os

        @feature: Operating System - Add architecture

        @assert: Operating System is updated with architecture

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

    def test_add_configtemplate(self):
        """@test: Add configtemplate to os

        @feature: Operating System - Add comfigtemplate

        @assert: Operating System is updated with config template

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

    def test_add_ptable(self):
        """@test: Add ptable to os

        @feature: Operating System - Add ptable

        @assert: Operating System is updated with ptable

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
