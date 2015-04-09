# -*- encoding: utf-8 -*-
"""Test class for Operating System CLI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.architecture import Architecture
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.template import Template
from robottelo.cli.factory import (
    CLIFactoryError,
    make_architecture,
    make_medium,
    make_os,
    make_partition_table,
    make_template,
)
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase


POSITIVE_CREATE_DATA = (
    {'name': gen_string("latin1")},
    {'name': gen_string("utf8")},
    {'name': gen_string("alpha")},
    {'name': gen_string("alphanumeric")},
    {'name': gen_string("numeric")},
    {'name': gen_string("html")},
)

NEGATIVE_CREATE_DATA = (
    {'name': gen_string("latin1", 300)},
    {'name': gen_string("utf8", 300)},
    {'name': gen_string("alpha", 300)},
    {'name': gen_string("alphanumeric", 300)},
    {'name': gen_string("numeric", 300)},
    {'name': gen_string("alphanumeric", 300)},
    {'name': " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': gen_string("latin1")},
     {'name': gen_string("latin1")}),
    ({'name': gen_string("utf8")},
     {'name': gen_string("utf8")}),
    ({'name': gen_string("alpha")},
     {'name': gen_string("alpha")}),
    ({'name': gen_string("alphanumeric")},
     {'name': gen_string("alphanumeric")}),
    ({'name': gen_string("numeric")},
     {'name': gen_string("numeric")}),
    ({'name': gen_string("utf8")},
     {'name': gen_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': gen_string("latin1")},
     {'name': gen_string("latin1", 300)}),
    ({'name': gen_string("utf8")},
     {'name': gen_string("utf8", 300)}),
    ({'name': gen_string("alpha")},
     {'name': gen_string("alpha", 300)}),
    ({'name': gen_string("alphanumeric")},
     {'name': gen_string("alphanumeric", 300)}),
    ({'name': gen_string("numeric")},
     {'name': gen_string("numeric", 300)}),
    ({'name': gen_string("utf8")},
     {'name': " "}),
    ({'name': gen_string("utf8")},
     {'name': gen_string("html", 300)}),
)

POSITIVE_DELETE_DATA = (
    {'name': gen_string("latin1")},
    {'name': gen_string("utf8")},
    {'name': gen_string("alpha")},
    {'name': gen_string("alphanumeric")},
    {'name': gen_string("numeric")},
)

NEGATIVE_DELETE_DATA = (
    {'id': gen_string("alpha")},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)


@run_only_on('sat')
@ddt
class TestOperatingSystem(CLITestCase):
    """Test class for Operating System CLI."""

    # Issues
    @skip_if_bug_open('redmine', 4547)
    def test_redmine_4547(self):
        """@test: Search for newly created OS by name

        @feature: Operating System - List

        @assert: Operating System is created and listed

        @bz: redmine#4547

        """
        result = OperatingSys.list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)
        result = make_os()
        name = result['name']
        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list.stdout[0]['id']})

        self.assertEqual(result['id'], os_info.stdout['id'])
        result = OperatingSys.list()
        self.assertGreater(len(result.stdout), length)
        self.assertEqual(result.return_code, 0)

    def test_bugzilla_1051557(self):
        """@test: Update an Operating System's major version.

        @feature: Operating System - Update

        @assert: Operating System major version is updated

        """

        try:
            os = make_os()
        except CLIFactoryError as err:
            self.fail(err)

        # New value for major
        major = int(os['major-version']) + 1

        result = OperatingSys.update(
            {'id': os['id'], 'major': major})
        self.assertEqual(result.return_code, 0,
                         'Failed to update activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')

        result = OperatingSys.info({
            u'id': os['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to get info for OS')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')
        self.assertEqual(int(result.stdout['major-version']), major,
                         'OS major version was not updated')

    @skip_if_bug_open('bugzilla', 1203457)
    @skip_if_bug_open('bugzilla', 1200116)
    def test_bugzilla_1203457(self):
        """@test: Create an OS pointing to an arch, medium and partition table.

        @feature: Operating System - Create

        @assert: An operating system is created.

        @bz: 1203457, 1200116

        """
        architecture = make_architecture()
        medium = make_medium()
        ptable = make_partition_table()
        operating_system = make_os({
            u'architecture-ids': architecture['id'],
            u'medium-ids': medium['id'],
            u'partition-table-ids': ptable['id'],
        })

        result = OperatingSys.info({'id': operating_system['id']})
        self.assertEqual(result.return_code, 0)
        stdout = result.stdout
        for attr in (
                'architectures', 'installation-media', 'partition-tables'):
            self.assertEqual(len(stdout[attr]), 1)
        self.assertEqual(stdout['architectures'][0], architecture['name'])
        self.assertEqual(stdout['installation-media'][0], medium['name'])
        self.assertEqual(stdout['partition-tables'][0], ptable['name'])

    def test_list_1(self):
        """@test: Displays list for operating system

        @feature: Operating System - List

        @assert: Operating System is created and listed

        """
        result = OperatingSys.list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)

        name = gen_string("alpha", 10)
        result = make_os({'name': name})

        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list.stdout[0]['id']})

        self.assertEqual(result['id'], os_info.stdout['id'])
        result = OperatingSys.list()
        self.assertGreater(len(result.stdout), length)
        self.assertEqual(result.return_code, 0)

    def test_info_1(self):
        """@test: Displays info for operating system

        @feature: Operating System - Info

        @assert: Operating System is created and have the correct data

        """

        result = make_os()
        os_info = OperatingSys.info({'id': result['id']})

        # Info does not return major or minor but a concat of name,
        # major and minor
        self.assertEqual(result['id'], os_info.stdout['id'])
        self.assertEqual(result['name'], os_info.stdout['name'])
        self.assertEqual(
            str(result['major-version']),
            os_info.stdout['major-version']
        )
        self.assertEqual(
            str(result['minor-version']),
            os_info.stdout['minor-version']
        )

    @data(*POSITIVE_CREATE_DATA)
    def test_positive_create_1(self, test_data):
        """@test: Create Operating System for all variations of name

        @feature: Operating System - Positive Create

        @assert: Operating System is created and can be found

        """

        # Create a new object using factory method
        new_obj = make_os(test_data)

        # Can we find the new object?
        result = OperatingSys.info({'id': new_obj['id']})

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(result.stdout['name'], new_obj['name'])

    @data(*NEGATIVE_CREATE_DATA)
    def test_negative_create_1(self, test_data):
        """@test: Create Operating System using invalid names

        @feature: Operating System - Negative Create

        @assert: Operating System is not created

        """

        with self.assertRaises(Exception):
            make_os(test_data)

    @data(*POSITIVE_UPDATE_DATA)
    def test_positive_update_1(self, test_data):
        """@test: Positive update of system name

        @feature: Operating System - Positive Update

        @assert: Operating System is updated and can be found

        """

        # "Unpacks" values from tuple
        orig_dict, updates_dict = test_data

        # Create a new object passing @test_data to factory method
        new_obj = make_os(orig_dict)

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        # Update original test_data with new values
        updates_dict['id'] = new_obj['id']
        orig_dict.update(updates_dict)
        # Now update the Foreman object
        result = OperatingSys.update(orig_dict)
        self.assertEqual(result.return_code, 0, "Failed to update object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        result = OperatingSys.info({'id': new_obj['id']})

        # Verify that standard values are correct
        self.assertEqual(
            new_obj['id'], result.stdout['id'], "IDs should match")
        self.assertNotEqual(result.stdout['name'], new_obj['name'])
        # There should be some attributes changed now
        self.assertNotEqual(new_obj, result.stdout, "Object should be updated")

    @data(*NEGATIVE_UPDATE_DATA)
    def test_negative_update_1(self, test_data):
        """@test: Negative update of system name

        @feature: Operating System - Negative Update

        @assert: Operating System is not updated

        """

        # "Unpacks" values from tuple
        orig_dict, updates_dict = test_data

        # Create a new object passing @test_data to factory method
        new_obj = make_os(orig_dict)

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        # Update original data with new values
        updates_dict['id'] = new_obj['id']
        orig_dict.update(updates_dict)

        # Now update the Foreman object
        result = OperatingSys.update(orig_dict)
        self.assertNotEqual(
            result.return_code, 0,
            "Update command should have failed")
        self.assertGreater(
            len(result.stderr), 0, "There should be an exception here")

        # OS should not have changed
        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        self.assertEqual(
            new_obj['name'],
            result.stdout['name'],
            "Name should not be updated")

    @data(*POSITIVE_DELETE_DATA)
    def test_positive_delete_1(self, test_data):
        """@test: Successfully deletes Operating System

        @feature: Operating System - Positive Delete

        @assert: Operating System is deleted

        """

        # Create a new object passing @test_data to factory method
        new_obj = make_os(test_data)

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        # Now delete it...
        result = OperatingSys.delete(
            {'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to delete object")
        self.assertEqual(len(result.stderr), 0, "Should not get an error.")
        # ... and make sure it does not exist anymore
        result = OperatingSys.info({'id': new_obj['id']})
        self.assertNotEqual(
            result.return_code, 0, "Return code should not be zero")
        self.assertGreater(
            len(result.stderr), 0, "Should have gotten an error")
        self.assertEqual(result.stdout, {}, "Should not get any output")

    @data(*NEGATIVE_DELETE_DATA)
    def test_negative_delete_1(self, test_data):
        """@test: Not delete Operating System for invalid data

        @feature: Operating System - Negative Delete

        @assert: Operating System is not deleted

        """

        # Create a new object using default values
        new_obj = make_os()

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        # The delete method requires the ID which we will not pass
        result = OperatingSys.delete(test_data)
        self.assertNotEqual(result.return_code, 0, "Should not delete object")
        self.assertGreater(
            len(result.stderr), 0, "Should have gotten an error")

        # Now make sure that it still exists
        result = OperatingSys.info({'id': new_obj['id']})
        self.assertTrue(result.return_code == 0, "Failed to find object")
        self.assertEqual(new_obj['id'], result.stdout['id'])
        self.assertEqual(new_obj['name'], result.stdout['name'])

    def test_add_architecture(self):
        """@test: Add Architecture to os

        @feature: Operating System - Add architecture

        @assert: Operating System is updated with architecture

        """

        a_ob = make_architecture()

        result = Architecture.info({'id': a_ob['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        new_obj = make_os()
        result = OperatingSys.add_architecture({'id': new_obj['id'],
                                                'architecture-id': a_ob['id']})
        self.assertEqual(result.return_code, 0, "Failed to add architecture")
        self.assertEqual(
            len(result.stderr), 0, "Should not have gotten an error")

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(len(result.stdout['architectures']), 1)
        self.assertEqual(a_ob['name'], result.stdout['architectures'][0])

    def test_add_configtemplate(self):
        """@test: Add configtemplate to os

        @feature: Operating System - Add comfigtemplate

        @assert: Operating System is updated with config template

        """

        conf_obj = make_template()

        result = Template.info({'id': conf_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(conf_obj['name'], result.stdout['name'])

        new_obj = make_os()
        result = OperatingSys.add_config_template(
            {'id': new_obj['id'],
             'config-template': conf_obj['name']})
        self.assertEqual(result.return_code, 0, "Failed to add configtemplate")
        self.assertEqual(
            len(result.stderr), 0, "Should not have gotten an error")

        result = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(len(result.stdout['templates']), 1)
        template_name = result.stdout['templates'][0]
        self.assertTrue(template_name.startswith(conf_obj['name']))

    def test_add_ptable(self):
        """@test: Add ptable to os

        @feature: Operating System - Add ptable

        @assert: Operating System is updated with ptable

        """
        # Create a partition table.
        ptable_name = make_partition_table()['name']
        response = PartitionTable.info({'name': ptable_name})
        self.assertEqual(response.return_code, 0, response.stderr)
        self.assertEqual(len(response.stderr), 0, response.stderr)

        # Create an operating system.
        os_id = make_os()['id']
        response = OperatingSys.info({'id': os_id})
        self.assertEqual(response.return_code, 0, response.stderr)
        self.assertEqual(len(response.stderr), 0, response.stderr)

        # Add the partition table to the operating system.
        response = OperatingSys.add_ptable({
            'id': os_id,
            'partition-table': ptable_name,
        })
        self.assertEqual(response.return_code, 0, response.stderr)
        self.assertEqual(len(response.stderr), 0, response.stderr)

        # Verify that the operating system has a partition table.
        response = OperatingSys.info({'id': os_id})
        self.assertEqual(
            len(response.stdout['partition-tables']),
            1,
            response.stdout['partition-tables']
        )
        self.assertEqual(response.stdout['partition-tables'][0], ptable_name)
