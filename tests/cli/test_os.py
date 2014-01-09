# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System CLI
"""
import random
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

        result = OperatingSys().list()
        # Grab a random report
        report = random.choice(result.stdout)
        result = OperatingSys().info({'id': report['Id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(report['Id'], result.stdout['Id'])

    def test_delete(self):
        """
        Displays delete for operating system.
        """
        name = generate_name()
        report = []
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().list()
        for i in result.stdout:
            nm = name + " 1.1"
            if nm == i['Name']:
                    report.append(i)

        # Grab a random report
        result = OperatingSys().delete({'id': report[0]['Id']})
        self.assertEqual(result.return_code, 0)

    def test_update(self):
        """
         Displays update for operating system.
        """

        name = generate_name()
        report = []
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().list()
        for i in result.stdout:
            nm = name + " 1.1"
            if nm == i['Name']:
                    report.append(i)

        # Grab a random report
        result = OperatingSys().update({'id': report[0]['Id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'id': report[0]['Id']})
        self.assertEqual(result.return_code, 0)
