"""Test class for Fact  CLI

:Requirement: Fact

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Fact

:Assignee: rdrazny

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.fact import Fact
from robottelo.test import CLITestCase


class FactTestCase(CLITestCase):
    """Fact related tests."""

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_list_by_name(self):
        """Test Fact List

        :id: 83794d97-d21b-4482-9522-9b41053e595f

        :expectedresults: Fact List is displayed


        :CaseImportance: Critical
        """
        for fact in ('uptime', 'uptime_days', 'uptime_seconds', 'memoryfree', 'ipaddress'):
            with self.subTest(fact):
                args = {'search': f"fact={fact}"}
                facts = Fact().list(args)
                self.assertEqual(facts[0]['fact'], fact)

    @pytest.mark.tier1
    def test_negative_list_by_name(self):
        """Test Fact List failure

        :id: bd56d27e-59c0-4f35-bd53-2999af7c6946

        :expectedresults: Fact List is not displayed


        :CaseImportance: Critical
        """
        fact = gen_string('alpha')
        args = {'search': f"fact={fact}"}
        self.assertEqual(Fact().list(args), [], 'No records should be returned')
