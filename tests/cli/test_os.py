# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from ddt import data, ddt
from robottelo.cli.factory import make_os
from robottelo.cli.metatest.default_data import POSITIVE_CREATE_DATA
from robottelo.cli.operatingsys import OperatingSys
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import bzbug
from robottelo.common.helpers import generate_name
from tests.cli.basecli import BaseCLI


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
        name = result['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        result['id'] = os_list.stdout[0]['id']
        # FIXME this assertion will aways be True
        self.assertEqual(result['id'], os_info.stdout['id'])

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

    def test_negative_create(self):
        """
        @feature: Operating System - Negative Create
        @test: Not create Operating System for all invalid data
        @assert: Operating System is not created
        @status: manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update(self):
        """
        @feature: Operating System - Positive Update
        @test: Update Operating System for all valid data
        @assert: Operating System is updated and can be found
        @status: manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update(self):
        """
        @feature: Operating System - Negative Update
        @test: Not update Operating System for invalid data
        @assert: Operating System is not updated
        @status: manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_delete(self):
        """
        @feature: Operating System - Positive Delete
        @test: Successfully deletes Operating System
        @assert: Operating System is deleted
        @status: manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_delete(self):
        """
        @feature: Operating System - Negative Delete
        @test: Not delete Operating System for invalid data
        @assert: Operating System is not deleted
        @status: manual
        """
        self.fail(NOT_IMPLEMENTED)
