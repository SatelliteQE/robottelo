#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data
from ddt import ddt
from lib.cli.fact import Fact
from lib.common.helpers import generate_name
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestFact(BaseCLI):
    """
    Fact related tests.
    """

    @data(
        'uptime', 'uptime_days', 'uptime_seconds', 'memoryfree', 'ipaddress',
    )
    @attr('cli', 'fact')
    def test_list_success(self, fact):
        """
        basic `list` operation test.
        """

        args = {
            'search': "fact='%s'" % fact,
        }

        _ret = Fact().list(args)
        self.assertEqual(_ret[0]['Fact'], fact)

    @data(
        generate_name(), generate_name(), generate_name(), generate_name(),
    )
    @attr('cli', 'fact')
    def test_list_fail(self, fact):
        """
        basic `list` operation test.
        """

        args = {
            'search': "fact='%s'" % fact,
        }
        self.assertFalse(Fact().list(args))
