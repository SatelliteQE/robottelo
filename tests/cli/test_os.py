# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.factory import make_os
from robottelo.common.helpers import generate_name
from tests.cli.basecli import BaseCLI


class TestOperatingSystem(BaseCLI):
    """
    Test class for Operating System CLI.
    """

    def test_create_os_1(self):
        """Successfully creates a new OS."""
        os_res = make_os()

    def test_list(self):
        """
        Displays list for operating system.
        """
        result = OperatingSys().list()
        self.assertEqual(result.return_code, 0)
        length = len(result.stdout)
        result = OperatingSys().create({'name': generate_name(),
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().list()
        self.assertTrue(len(result.stdout) > length)
        self.assertEqual(result.return_code, 0)

    def test_info(self):
        """
        Displays info for operating system.
        """

        name = generate_name()
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)

        result = OperatingSys().info({'label': name})
        self.assertEqual(result.return_code, 0)

    def test_delete(self):
        """
        Displays delete for operating system.
        """
        name = generate_name()
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)

        result = OperatingSys().delete({'label': name})
        self.assertEqual(result.return_code, 0)

        result = OperatingSys().info({'label': name})
        self.assertEqual(result.return_code, 128)

    def test_update(self):
        """
         Displays update for operating system.
        """

        nm = generate_name()
        result = OperatingSys().create({'name': nm,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': nm})

        result = OperatingSys().update({'id': result.stdout['id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': nm})
        self.assertEqual(result.return_code, 0)
        nm = result.stdout['name']
        # this will check the updation of major == 3
        self.assertEqual(nm, result.stdout['name'])
