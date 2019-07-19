# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Reports CLI.

:Requirement: Report

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import random

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.report import Report
from robottelo.decorators import tier1, upgrade
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

    @tier1
    def test_positive_list(self):
        """Test list for Puppet report

        :id: 8325e18f-58a4-49b8-a5f3-eebbe1d568b5

        :expectedresults: Puppert Report List is displayed

        :CaseImportance: Critical
        """
        Report.list()

    @tier1
    def test_positive_info(self):
        """Test Info for Puppet report

        :id: 32646d4b-7101-421a-85e0-777d3c6b71ec

        :expectedresults: Puppet Report Info is displayed

        :CaseImportance: Critical
        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        result = Report.info({'id': report['id']})
        self.assertEqual(report['id'], result['id'])

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Check if Puppet Report can be deleted by its ID

        :id: bf918ec9-e2d4-45d0-b913-ab939b5d5e6a

        :expectedresults: Puppet Report is deleted

        :CaseImportance: Critical
        """
        result = Report.list()
        self.assertGreater(len(result), 0)
        # Grab a random report
        report = random.choice(result)
        Report.delete({'id': report['id']})
        with self.assertRaises(CLIReturnCodeError):
            Report.info({'id': report['id']})
