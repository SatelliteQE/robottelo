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

    def _create_os(self, name=None, major=None, minor=None):
        """
        Creates the operating system
        """
        name = name if name else generate_name()
        major = major if major else random.randint(0, 10)
        minor = minor if minor else random.randint(0, 10)

        args = {
            'name': name,
            'major': major,
            'minor': minor,
        }

        OperatingSys().create(args)
        self.assertTrue(OperatingSys().exists(('name', args['name'])))

    def test_create_os_1(self):
        """Successfully creates a new OS."""

        self._create_os()

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

        name = generate_name()
        result = OperatingSys().create({'name': name,
                                        'major': 1, 'minor': 1})
        self.assertTrue(result.return_code == 0,
                        "Operating system create - retcode")
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': name})

        result = OperatingSys().update({'id': result.stdout['id'], 'major': 3})
        self.assertEqual(result.return_code, 0)
        result = OperatingSys().info({'label': name})
        self.assertEqual(result.return_code, 0)
        # this will check the updation of major == 3
        self.assertEqual(name + " 3.1", result.stdout['name'])
