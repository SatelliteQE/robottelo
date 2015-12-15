# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Reports CLI."""

import random

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.report import Report
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


class ReportTestCase(CLITestCase):
    """Test class for Reports CLI. """

    def setUp(self):
        super(ReportTestCase, self).setUp()
        self.run_puppet_agent()

    def run_puppet_agent(self):
        """Retrieves the client configuration from the puppet master and
        applies it to the local host. This is required to make sure
        that we have reports available.
        """
        ssh.command('puppet agent -t')

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """@Test: Test list for Puppet report

        @Feature: Puppet Report

        @Assert: Puppert Report List is displayed
        """
        Report.list()

    @run_only_on('sat')
    @tier1
    def test_positive_info(self):
        """@Test: Test Info for Puppet report

        @Feature: Puppet Report

        @Assert: Puppet Report Info is displayed
        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        result = Report.info({'id': report['id']})
        self.assertEqual(report['id'], result['id'])

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Check if Puppet Report can be deleted by its ID

        @Feature: Puppet Report

        @Assert: Puppet Report is deleted
        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        Report.delete({'id': report['id']})
        with self.assertRaises(CLIReturnCodeError):
            Report.info({'id': report['id']})
