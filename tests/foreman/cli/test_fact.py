"""Test class for Fact  CLI"""

from fauxfactory import gen_string
from robottelo.cli.fact import Fact
from robottelo.decorators import run_only_on, stubbed
from robottelo.test import CLITestCase


class TestFact(CLITestCase):
    """Fact related tests."""

    @stubbed('Need to create facts before we can check them.')
    @run_only_on('sat')
    def test_list_success(self):
        """@Test: Test Fact List

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
    def test_list_fail(self):
        """@Test: Test Fact List failure

        @Feature: Fact - List Negative

        @Assert: Fact List is not displayed

        """
        fact = gen_string('alpha')
        args = {'search': "fact='%s'" % fact}
        self.assertEqual(
            Fact().list(args), [], 'No records should be returned')
