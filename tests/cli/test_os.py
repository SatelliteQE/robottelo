# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.factory import make_os
from robottelo.common.helpers import generate_name, generate_string
from robottelo.common.decorators import bzbug
from tests.cli.basecli import MetaCLI


class TestOperatingSystem(MetaCLI):
    """
    Test class for Operating System CLI.
    """

    factory = make_os
    factory_obj = OperatingSys

    # Overide defaults from metaclass
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

    def test_create_os_1(self):
        """Successfully creates a new OS."""
        os_res = make_os()
        name = os_res['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        os_res['id'] = os_list.stdout[0]['id']
        self.assertEqual(os_res['id'], os_info.stdout['id'])

    def test_list(self):
        """
        Displays list for operating system.
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
        Displays info for operating system.
        """

        result = make_os()
        name = result['name']
        os_list = OperatingSys().list({'search': 'name=%s' % name})
        os_info = OperatingSys().info({'id': os_list.stdout[0]['id']})
        result['id'] = os_list.stdout[0]['id']
        self.assertEqual(result['id'], os_info.stdout['id'])

    def test_delete(self):
        """
        Displays delete for operating system.
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
         Displays update for operating system.
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

    def test_positive_create(self):
        """
         Successfully creates object FOREMAN_OBJECT.

         1. Create a new Foreman object using the a base factory using
         2. Assert that the object was created and can be found;
         @return: Asserts that object can be created.
        """

        #Create a new object using factory method
        new_obj = self.factory()

        search_key = "%(name)s %(minor)s.%(major)s" % (new_obj)
        # Can we find the new object?
        result = self.factory_obj().exists((self.search_key,
                                            new_obj[self.search_key]))

        self.assertTrue(result.return_code == 0, "Failed to create object")
        self.assertTrue(len(result.stderr) == 0,
                        "There should not be an exception here")
        name = result.stdout[self.search_key].split(' ')
        self.assertEqual(new_obj[self.search_key], name[0])

    def test_negative_create(self):
        self.fails("Please fix these tests.")

    def test_positive_update(self):
        self.fails("Please fix these tests.")

    def test_negative_update(self):
        self.fails("Please fix these tests.")

    def test_negative_delete(self):
        self.fails("Please fix these tests.")
