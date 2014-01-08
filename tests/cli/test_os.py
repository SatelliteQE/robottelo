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

        result = OperatingSys().list()
        # Grab a random report
        report = random.choice(result.stdout)
        result = OperatingSys().delete({'id': report['Id']})
        self.assertEqual(result.return_code, 0)

    def test_update(self):
        """
         Displays update for operating system.
        """

        result = OperatingSys().list()
        # Grab a random report
        report = random.choice(result.stdout)
        result = OperatingSys().update({'id': report['Id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'id': report['Id']})
        self.assertEqual(result.return_code, 0)
