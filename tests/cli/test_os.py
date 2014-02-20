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
        os_info = OperatingSys().info({'label': os_res['name']})
        os_res['name'] = os_info.stdout['name']
        self.assertEqual(os_res['name'], os_info.stdout['name'])

    def test_list(self):
        """
        Displays list for operating system.
        """
        result = OperatingSys().list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)
        result = make_os()
        os_info = OperatingSys().info({'label': result['name']})
        result['name'] = os_info.stdout['name']
        self.assertEqual(result['name'], os_info.stdout['name'])
        result = OperatingSys().list()
        self.assertTrue(len(result.stdout) > length)
        self.assertEqual(result.return_code, 0)

    def test_info(self):
        """
        Displays info for operating system.
        """

        result = make_os()
        os_info = OperatingSys().info({'label': result['name']})
        result['name'] = os_info.stdout['name']
        self.assertEqual(result['name'], os_info.stdout['name'])

        name = result['name'].split(" ")
        result = OperatingSys().info({'label': name[0]})
        self.assertEqual(result.return_code, 0)

    def test_delete(self):
        """
        Displays delete for operating system.
        """
        result = make_os()
        os_info = OperatingSys().info({'label': result['name']})
        result['name'] = os_info.stdout['name']
        self.assertEqual(result['name'], os_info.stdout['name'])

        name = result['name'].split(" ")
        result = OperatingSys().delete({'label': name[0]})
        self.assertEqual(result.return_code, 0)

        result = OperatingSys().info({'label': name[0]})
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
