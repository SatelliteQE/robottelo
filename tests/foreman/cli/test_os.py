# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from ddt import data, ddt
from robottelo.cli.factory import make_os
from robottelo.cli.operatingsys import OperatingSys
from robottelo.common.decorators import bzbug, redminebug
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


POSITIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 10)},
    {'name': generate_string("utf8", 10)},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
    {'name': generate_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 300)},
    {'name': generate_string("utf8", 300)},
    {'name': generate_string("alpha", 300)},
    {'name': generate_string("alphanumeric", 300)},
    {'name': generate_string("numeric", 300)},
    {'name': generate_string("alphanumeric", 300)},
    {'name': " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': generate_string("latin1", 10)},
     {'name': generate_string("latin1", 10)}),
    ({'name': generate_string("utf8", 10)},
     {'name': generate_string("utf8", 10)}),
    ({'name': generate_string("alpha", 10)},
     {'name': generate_string("alpha", 10)}),
    ({'name': generate_string("alphanumeric", 10)},
     {'name': generate_string("alphanumeric", 10)}),
    ({'name': generate_string("numeric", 10)},
     {'name': generate_string("numeric", 10)}),
    ({'name': generate_string("utf8", 10)},
     {'name': generate_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': generate_string("latin1", 10)},
     {'name': generate_string("latin1", 300)}),
    ({'name': generate_string("utf8", 10)},
     {'name': generate_string("utf8", 300)}),
    ({'name': generate_string("alpha", 10)},
     {'name': generate_string("alpha", 300)}),
    ({'name': generate_string("alphanumeric", 10)},
     {'name': generate_string("alphanumeric", 300)}),
    ({'name': generate_string("numeric", 10)},
     {'name': generate_string("numeric", 300)}),
    ({'name': generate_string("utf8", 10)},
     {'name': " "}),
    ({'name': generate_string("utf8", 10)},
     {'name': generate_string("html", 300)}),
)

POSITIVE_DELETE_DATA = (
    {'name': generate_string("latin1", 10)},
    {'name': generate_string("utf8", 10)},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
)

NEGATIVE_DELETE_DATA = (
    {'id': generate_string("alpha", 10)},
    {'id': None},
    {'id': ""},
    {},
    {'id': -1},
)


@ddt
class TestOperatingSystem(BaseCLI):
    """
    Test class for Operating System CLI.
    """

    # Issues
    @redminebug('4547')
    def test_redmine_4547(self):
        """
        @test: Search for newly created OS by name
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

    @bzbug('1051557')
    def test_bugzilla_1051557(self):
        """
        @test: Update an Operating System's major version.
        @feature: Operating System - Update
        @assert: Operating System major version is updated
        @bz: 1021557
        """

        new_obj = make_os()
        os_info = OperatingSys.info({'id': new_obj['id']})
        self.assertEqual(new_obj['name'], os_info.stdout['name'])

        # New value for major
        major = int(new_obj['major']) + 1
        result = OperatingSys.update(
            {'id': os_info.stdout['id'], 'major': major})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys.info({'id': result.stdout['id']})
        self.assertEqual(result.return_code, 0)
        # this will check the updation of major == 3
        self.assertEqual(major, result.stdout['major'])

    def test_list_1(self):
        """
        @test: Displays list for operating system
        @feature: Operating System - List
        @assert: Operating System is created and listed
        """
        result = OperatingSys.list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)

        name = generate_string("alpha", 10)
        result = make_os({'name': name})

        os_list = OperatingSys.list({'search': 'name=%s' % name})
        os_info = OperatingSys.info({'id': os_list.stdout[0]['id']})

        self.assertEqual(result['id'], os_info.stdout['id'])
        result = OperatingSys.list()
        self.assertGreater(len(result.stdout), length)
        self.assertEqual(result.return_code, 0)

    def test_info_1(self):
        """
        @test: Displays info for operating system
        @feature: Operating System - Info
        @assert: Operating System is created and have the correct data
        """

        result = make_os()
        os_info = OperatingSys.info({'id': result['id']})

        # Info does not return major or minor but a concat of name,
        # major and minor
        self.assertEqual(result['id'], os_info.stdout['id'])
        self.assertEqual(result['name'], os_info.stdout['name'])
        self.assertIn(str(result['major']), os_info.stdout['name'])
        self.assertIn(str(result['minor']), os_info.stdout['name'])

    @data(*POSITIVE_CREATE_DATA)
    def test_positive_create_1(self, test_data):
        """
        @test: Create Operating System for all variations of name
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
        """
        @test: Create Operating System using invalid names
        @feature: Operating System - Negative Create
        @assert: Operating System is not created
        """

        with self.assertRaises(Exception):
            make_os(test_data)

    @data(*POSITIVE_UPDATE_DATA)
    def test_positive_update_1(self, test_data):
        """
        @test: Positive update of system name
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
        """
        @test: Negative update of system name
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
        """
        @test: Successfully deletes Operating System
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
        self.assertEqual(result.stdout, [], "Should not get any output")

    @data(*NEGATIVE_DELETE_DATA)
    def test_negative_delete_1(self, test_data):
        """
        @test: Not delete Operating System for invalid data
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
