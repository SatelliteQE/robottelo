"""Test class for Fact  CLI"""

from fauxfactory import gen_string
from robottelo.cli.fact import Fact
from robottelo.decorators import run_only_on, stubbed, tier1
from robottelo.test import CLITestCase


class FactTestCase(CLITestCase):
    """Fact related tests."""

    @stubbed('Need to create facts before we can check them.')
    @run_only_on('sat')
    @tier1
    def test_positive_list_by_name(self):
        """Test Fact List

        @Feature: Fact - List Positive

        @Assert: Fact List is displayed

        """
        for fact in ('uptime', 'uptime_days', 'uptime_seconds', 'memoryfree',
                     'ipaddress'):
            with self.subTest(fact):
                args = {'search': "fact='%s'" % fact}
                facts = Fact().list(args)
                self.assertEqual(facts[0]['fact'], fact)

    @run_only_on('sat')
    @tier1
    def test_negative_list_by_name(self):
        """Test Fact List failure

        @Feature: Fact - List Negative

        @Assert: Fact List is not displayed

        """
        fact = gen_string('alpha')
        args = {'search': "fact='%s'" % fact}
        self.assertEqual(
            Fact().list(args), [], 'No records should be returned')
