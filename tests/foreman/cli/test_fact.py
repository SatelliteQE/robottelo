# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Fact  CLI"""

import sys

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.cli.fact import Fact
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string
from robottelo.test import CLITestCase

if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


@ddt
class TestFact(CLITestCase):
    """Fact related tests."""

    @unittest.skip("Need to create facts before we can check them.")
    @data(
        'uptime', 'uptime_days', 'uptime_seconds', 'memoryfree', 'ipaddress',
    )
    @attr('cli', 'fact')
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
        generate_string("alpha", 10),
        generate_string("alpha", 10),
        generate_string("alpha", 10),
        generate_string("alpha", 10),
    )
    @attr('cli', 'fact')
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
