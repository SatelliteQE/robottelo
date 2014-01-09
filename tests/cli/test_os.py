# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
from robottelo.cli.operatingsys import OperatingSys
from robottelo.common.helpers import generate_name
from tests.cli.basecli import BaseCLI


class TestOperatingSystem(BaseCLI):
    """
    Test class for Operating System CLI.
    """

    def test_create(self):
        """
        Creates the operating system
        """

        result = OperatingSys().create({'name': generate_name(),
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)

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

        # Grab a random report
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

        # Grab a random report
        result = OperatingSys().delete({'label': name})
        self.assertEqual(result.return_code, 0)

    def test_update(self):
        """
         Displays update for operating system.
        """

        name = generate_name()
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': name})

        # Grab a random report
        result = OperatingSys().update({'id': result.stdout['Id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': name})
        self.assertEqual(result.return_code, 0)
