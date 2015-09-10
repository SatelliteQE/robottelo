# -*- encoding: utf-8 -*-
"""Test class for Fact  CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.fact import Fact
from robottelo.decorators import data, run_only_on, stubbed
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestFact(CLITestCase):
    """Fact related tests."""

    @stubbed('Need to create facts before we can check them.')
    @data(
        'uptime', 'uptime_days', 'uptime_seconds', 'memoryfree', 'ipaddress',
    )
    def test_list_success(self, fact):
        """@Test: Test Fact List

        @Feature: Fact - List Positive

        @Assert: Fact List is displayed

        """

        args = {
            'search': "fact='%s'" % fact,
        }

        result = Fact().list(args)
        stdout = result.stdout

        self.assertEqual(stdout[0]['fact'], fact)

    @data(
        gen_string("alpha", 10),
        gen_string("alpha", 10),
        gen_string("alpha", 10),
        gen_string("alpha", 10),
    )
    def test_list_fail(self, fact):
        """@Test: Test Fact List failure

        @Feature: Fact - List Negative

        @Assert: Fact List is not displayed

        """

        args = {
            'search': "fact='%s'" % fact,
        }
        self.assertEqual(
            Fact().list(args).stdout, [], "No records should be returned")
