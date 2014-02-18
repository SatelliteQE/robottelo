# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from ddt import data, ddt
from robottelo.cli.factory import make_os
from robottelo.cli.operatingsys import OperatingSys
from robottelo.common.decorators import bzbug
from robottelo.common.helpers import generate_name, generate_string
from tests.cli.basecli import BaseCLI


POSITIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 10).encode("utf-8")},
    {'name': generate_string("utf8", 10).encode("utf-8")},
    {'name': generate_string("alpha", 10)},
    {'name': generate_string("alphanumeric", 10)},
    {'name': generate_string("numeric", 10)},
    {'name': generate_string("html", 10)},
)

NEGATIVE_CREATE_DATA = (
    {'name': generate_string("latin1", 300).encode("utf-8")},
    {'name': " "},
    {'': generate_string("alpha", 10)},
    {generate_string("alphanumeric", 10): " "},
)

POSITIVE_UPDATE_DATA = (
    ({'name': generate_string("latin1", 10).encode("utf-8")},
     {'name': generate_string("latin1", 10).encode("utf-8")}),
    ({'name': generate_string("utf8", 10).encode("utf-8")},
     {'name': generate_string("utf8", 10).encode("utf-8")}),
    ({'name': generate_string("alpha", 10)},
     {'name': generate_string("alpha", 10)}),
    ({'name': generate_string("alphanumeric", 10)},
     {'name': generate_string("alphanumeric", 10)}),
    ({'name': generate_string("numeric", 10)},
     {'name': generate_string("numeric", 10)}),
    ({'name': generate_string("utf8", 10).encode("utf-8")},
     {'name': generate_string("html", 6)}),
)

NEGATIVE_UPDATE_DATA = (
    ({'name': generate_string("utf8", 10).encode("utf-8")},
     {'name': generate_string("utf8", 300).encode("utf-8")}),
    ({'name': generate_string("utf8", 10).encode("utf-8")},
     {'name': ""}),
)

POSITIVE_DELETE_DATA = (
    {'name': generate_string("latin1", 10).encode("utf-8")},
    {'name': generate_string("utf8", 10).encode("utf-8")},
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

    factory_obj = OperatingSys
    search_key = 'name'

    def test_create_os_1(self):
        """
        @feature: Operating System - Create
        @test: Successfully creates a new Operating System
        @assert: Operating System is created and can be found
        """
        os_res = make_os()
        name = os_res['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        os_res['id'] = os_list.stdout[0]['id']
        self.assertEqual(os_res['id'], os_info.stdout['id'])

    def test_list(self):
        """
        @feature: Operating System - List
        @test: Displays list for operating system
        @assert: Operating System is created and listed
        """
        result = OperatingSys().list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)
        result = make_os()
        name = result['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        result['id'] = os_list.stdout[0]['id']
        self.assertEqual(result['id'], os_info.stdout['id'])
        result = OperatingSys().list()
        self.assertTrue(len(result.stdout) > length)
        self.assertEqual(result.return_code, 0)

    def test_info(self):
        """
        @feature: Operating System - Info
        @test: Displays info for operating system
        @assert: Operating System is created and have the correct data
        """

        result = make_os()
        os_list = OperatingSys().list({'search': 'name=%s' % result['name']})
        # Add the created OS id
        result['id'] = os_list.stdout[0]['id']
        os_info = OperatingSys().info({'id': result['id']})

        parts = os_info.stdout['name'].split()
        name = parts[0]
        major, minor = (int(number) for number in parts[1].split('.'))

        self.assertEqual(result['id'], os_info.stdout['id'])
        self.assertEqual(result['name'], name)
        self.assertEqual(result['major'], major)
        self.assertEqual(result['minor'], minor)

    def test_delete(self):
        """
        @feature: Operating System - Delete
        @test: Delete Operating System
        @assert: Operating System is created and deleted
        """
        result = make_os()
        name = result['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        result['id'] = os_list.stdout[0]['id']
        self.assertEqual(result['id'], os_info.stdout['id'])

        del_id = os_list.stdout[0]['id']
        result = OperatingSys().delete({'id': del_id})
        self.assertEqual(result.return_code, 0)

        result = OperatingSys().info({'id': del_id})
        self.assertEqual(result.return_code, 128)
        self.assertTrue(len(result.stderr) > 0)

    @bzbug('1051557')
    def test_update(self):
        """
        @feature: Operating System - Update
        @test: Update an Operating System.
        @assert: Operating System is updated
        @bz: 1021557
        """

        name = generate_name()
        result = make_os()
        os_info = OperatingSys().info({'label': result['name']})
        result['name'] = os_info.stdout['name']
        self.assertEqual(result['name'], os_info.stdout['name'])
        result = OperatingSys().info({'label': name})

        result = OperatingSys().update({'id': result.stdout['id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': name})
        self.assertEqual(result.return_code, 0)
        name = result.stdout['name']
        major = result.stdout['major']
        # this will check the updation of major == 3
        self.assertEqual(name, result.stdout['name'])
        self.assertEqual(major, result.stdout['major'])

    @data(*POSITIVE_CREATE_DATA)
    def test_positive_create(self, data):
        """
        @feature: Operating System - Positive Create
        @test: Create Operating System for all variations of name
        @assert: Operating System is created and can be found
        """

        #Create a new object using factory method
        new_obj = make_os(data)

        # Can we find the new object?
        result = self.factory_obj().exists((self.search_key,
                                            new_obj[self.search_key]))

        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(len(result.stderr) == 0,
                        "There should not be an exception here")
        name = result.stdout[self.search_key].split(' ')[0]
        self.assertEqual(new_obj[self.search_key], name)

    @data(*NEGATIVE_CREATE_DATA)
    def test_negative_create(self, data):
        """
        @feature: Operating System - Negative Create
        @test: Not create Operating System for all invalid data
        @assert: Operating System is not created
        """

        # Try to create a new object passing @data to factory method
        new_obj = self.factory_obj().create(data)
        self.assertFalse(
            new_obj.return_code == 0, "Object should not be created")
        self.assertTrue(
            len(new_obj.stderr) > 0, "Should have raised an exception")

    @data(*POSITIVE_UPDATE_DATA)
    def test_positive_update(self, data):
        """
        @feature: Operating System - Positive Update
        @test: Update Operating System for all valid data
        @assert: Operating System is updated and can be found
        """

        # "Unpacks" values from tuple
        orig_dict, updates_dict = data

        # Create a new object passing @data to factory method
        new_obj = make_os(orig_dict)

        result = self.factory_obj().exists(
            (self.search_key, new_obj[self.search_key])
        )
        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")

        name = result.stdout[self.search_key].split()[0]
        self.assertEqual(
            new_obj[self.search_key], name)

        # Store the new object for future assertions and to use its ID
        new_obj = result.stdout

        # Update original data with new values
        orig_dict['id'] = result.stdout['id']
        orig_dict.update(updates_dict)
        # Now update the Foreman object
        result = self.factory_obj().update(orig_dict)
        self.assertTrue(result.return_code == 0, "Failed to update object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")

        result = self.factory_obj().info({'id': new_obj['id']})

        # Verify that standard values are correct
        self.assertEqual(
            new_obj['id'], result.stdout['id'], "IDs should match")
        self.assertNotEqual(
            new_obj[self.search_key], result.stdout[self.search_key])
        # There should be some attributes changed now
        self.assertNotEqual(new_obj, result.stdout, "Object should be updated")

    @data(*NEGATIVE_UPDATE_DATA)
    def test_negative_update(self, data):
        """
        @feature: Operating System - Negative Update
        @test: Not update Operating System for invalid data
        @assert: Operating System is not updated
        """

        # "Unpacks" values from tuple
        orig_dict, updates_dict = data

        # Create a new object passing @data to factory method
        new_obj = make_os(orig_dict)

        result = self.factory_obj().exists(
            (self.search_key, new_obj[self.search_key])
        )
        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(
            len(result.stderr) == 0, "There should not be an exception here")

        name = result.stdout[self.search_key].split()[0]
        self.assertEqual(new_obj[self.search_key], name)

        # Store the new object for future assertionss and to use its ID
        new_obj = result.stdout

        # Update original data with new values
        orig_dict['id'] = int(result.stdout['id'])
        orig_dict.update(updates_dict)

        # Now update the Foreman object
        result = self.factory_obj().update(orig_dict)
        self.assertFalse(
            result.return_code == 0, "%s, %s" % (data, result.stdout))
        self.assertTrue(len(result.stderr) > 0, "There should be errors")

        # Use the name to search because the new_obj['name'] is concatenated
        # with the version because the command output
        result = self.factory_obj().exists(
            (self.search_key, name)
        )
        # Verify that new values were not updated
        self.assertEqual(
            new_obj, result.stdout, "Object should not be updated")

    @data(*POSITIVE_DELETE_DATA)
    def test_positive_delete(self, data):
        """
        @feature: Operating System - Positive Delete
        @test: Successfully deletes Operating System
        @assert: Operating System is deleted
        """

        # Create a new object passing @data to factory method
        new_obj = make_os(data)

        result = self.factory_obj().exists(
            (self.search_key, new_obj[self.search_key])
        )
        self.assertTrue(result.return_code == 0, "Failed to create object")

        # Store the new object for future assertionss and to use its ID
        new_obj = result.stdout

        # Now delete it...
        result = self.factory_obj().delete(
            {'id': new_obj['id']})
        self.assertTrue(result.return_code == 0, "Failed to delete object")
        self.assertTrue(len(result.stderr) == 0, "Should not get an error.")
        # ... and make sure it does not exist anymore
        result = self.factory_obj().info({'id': new_obj['id']})
        self.assertFalse(
            result.return_code == 0, "Return code should not be zero")
        self.assertTrue(len(result.stderr) > 0, "Should have gotten an error")
        self.assertEqual(result.stdout, [], "Should not get any output")

    @data(*NEGATIVE_DELETE_DATA)
    def test_negative_delete(self, data):
        """
        @feature: Operating System - Negative Delete
        @test: Not delete Operating System for invalid data
        @assert: Operating System is not deleted
        """

        # Create a new object using default values
        new_obj = make_os()

        result = self.factory_obj().exists(
            (self.search_key, new_obj[self.search_key])
        )
        self.assertTrue(result.return_code == 0, "Failed to create object")
        # Store the name because the output concatenate the name and version
        name = new_obj[self.search_key]
        # Store the new object for further assertions
        new_obj = result.stdout

        # Now try to delete it...
        result = self.factory_obj().delete(data)
        self.assertFalse(result.return_code == 0, "Should not delete object")
        self.assertTrue(len(result.stderr) > 0, "Should have gotten an error")
        # Now make sure that it still exists

        result = self.factory_obj().exists(
            (self.search_key, name)
        )
        self.assertTrue(result.return_code == 0, "Failed to find object")
        self.assertEqual(new_obj, result.stdout)
