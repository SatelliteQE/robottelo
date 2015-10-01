# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Reports CLI."""

import random

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.report import Report
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestReport(CLITestCase):
    """Test class for Reports CLI. """

    def setUp(self):
        super(TestReport, self).setUp()
        self.run_puppet_agent()

    def run_puppet_agent(self):
        """Retrieves the client configuration from the puppet master and
        applies it to the local host. This is required to make sure
        that we have reports available.

        """
        ssh.command('puppet agent -t')

    def test_list(self):
        """@Test: Test list for Puppet report

        @Feature: Puppet Report - list

        @Assert: Puppert Report List is displayed

        """
        Report.list()

    def test_info(self):
        """@Test: Test Info for Puppet report

        @Feature: Puppet Report - Info

        @Assert: Puppet Report Info is displayed

        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        result = Report.info({'id': report['id']})
        self.assertEqual(report['id'], result['id'])

    def test_delete(self):
        """@Test: Check if Puppet Report can be deleted

        @Feature: Puppet Report - Delete

        @Assert: Puppet Report is deleted

        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        Report.delete({'id': report['id']})
        with self.assertRaises(CLIReturnCodeError):
            Report.info({'id': report['id']})
