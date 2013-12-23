#!/usr/bin/env python
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
        Displays list for puppet report.
        """

        self.run_puppet_agent()

        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertTrue(len(result.stdout) > 0)

    def test_info(self):
        """
        Displays info for puppet report.
        """
        self.run_puppet_agent()

        result = Report().list()

        # Grab a random report
        report = random.choice(result.stdout)
        result = Report().info({'id': report['Id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(report['Id'], result.stdout['Id'])

    def test_delete(self):
        """
        Delete a puppet report.
        """
        self.run_puppet_agent()

        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertTrue(len(result.stdout) > 0)

        # Grab a random report
        report = random.choice(result.stdout)
        result = Report().delete({'id': report['Id']})
        self.assertEqual(result.return_code, 0)
        result = Report().info({'id': report['Id']})
        self.assertTrue(result.stderr)
