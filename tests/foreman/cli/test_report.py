# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Reports CLI.
"""

import random

from tests.cli.basecli import BaseCLI
from robottelo.cli.report import Report
from robottelo.common import ssh


class TestReport(BaseCLI):
    """
    Test class for Reports CLI.
    """

    def run_puppet_agent(self):
        """
        Retrieves the client configuration from the puppet master and
        applies it to the local host. This is required to make sure
        that we have reports available.
        """

        ssh.command('puppet agent -t')

    def test_list(self):
        """
        @Feature: Puppet Report - list
        @Test: Test list for Puppet report
        @Assert: Puppert Report List is displayed
        """

        self.run_puppet_agent()

        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertTrue(len(result.stdout) > 0)

    def test_info(self):
        """
        @Feature: Puppet Report - Info
        @Test: Test Info for Puppet report
        @Assert: Puppet Report Info is displayed
        """
        self.run_puppet_agent()

        result = Report().list()

        # Grab a random report
        report = random.choice(result.stdout)
        result = Report().info({'id': report['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(report['id'], result.stdout['id'])

    def test_delete(self):
        """
        @Feature: Puppet Report- Delete
        @Test: Check if Puppet Report can be deleted
        @Assert: Puppet Report is deleted
        """
        self.run_puppet_agent()

        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertTrue(len(result.stdout) > 0)

        # Grab a random report
        report = random.choice(result.stdout)
        result = Report().delete({'id': report['id']})
        self.assertEqual(result.return_code, 0)
        result = Report().info({'id': report['id']})
        self.assertTrue(result.stderr)
