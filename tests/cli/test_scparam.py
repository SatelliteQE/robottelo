# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Smart Class Parameter CLI.
"""

import random

from tests.cli.basecli import BaseCLI
from robottelo.cli.smartclass import SmartClassParameter
from robottelo.common import ssh
from robottelo.common.decorators import bzbug


class TestSmartClassParameter(BaseCLI):
    """
    Test class for Smart Class Parameter CLI.
    """

    def run_puppet_module(self):
        """
        Import some parameterized puppet class. This is required to make sure
        that we have smart class variable available.
        """

        ssh.command('puppet module install --force puppetlabs/ntp')

    @bzbug('1047794')
    def test_info(self):
        """
        @Feature: SmartClass Paramter - Info
        @Test: Check if SmartClass Paramter Info is displayed
        @Assert: SmartClass Paramter Info is displayed
        """
        self.run_puppet_module()
        result = SmartClassParameter().list()

        self.assertTrue(len(result.stdout) > 0)
        self.assertEqual(result.return_code, 0)

        sc_param = random.choice(result.stdout)
        res = SmartClassParameter().info({'id': sc_param['id']})
        self.assertEqual(sc_param['id'], res.stdout['id'])
        self.assertEqual(res.return_code, 0)
