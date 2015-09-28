# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for PuppetModule CLI"""

from robottelo.cli.puppetmodule import PuppetModule
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestPuppetModule(CLITestCase):
    """Tests for PuppetModule via Hammer CLI"""

    @skip_if_bug_open('bugzilla', 1127382)
    def test_bugzilla_1127382(self):
        """@Test: hammer puppet-module <info,list> --help

        @Feature: puppet-module info/list

        @Assert: Assert product option are present

        """
        # puppet-module list --help:
        result = PuppetModule.list({'help': True})
        # get list of lines and check they all are unique
        lines = [line['message'] for line in result]
        self.assertEqual(len(set(lines)), len(lines),
                         'The help should not have repeat options')
        product_options = [line for line in lines
                           if line.startswith('--product')]
        self.assertGreater(len(product_options), 0,
                           'At least one --product option should be present')

        # puppet-module info --help:info, ignore exception
        result = PuppetModule.info({'help': True})
        # get list of lines and check they all are unique
        lines = [line for line in result['options']]
        self.assertEqual(len(set(lines)), len(lines),
                         'The help should not have repeat options')
        product_options = [line for line in lines
                           if line.startswith('--product')]
        self.assertGreater(len(product_options), 0,
                           'At least one --product option should be present')
