# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

"""
Test class for PuppetModule CLI
"""

from robottelo.test import CLITestCase
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.common.decorators import skip_if_bug_open


class TestPuppetModule(CLITestCase):
    """
    Tests for PuppetModule via Hammer CLI
    """

    @skip_if_bug_open('bugzilla', 1127382)
    def test_list_puppetmodule(self):
        """
        @Test: Check if a puppet module is listed
        @Feature: Puppet - Module
        @Assert: Puppet module is listed
        """

        result = PuppetModule.list()
        self.assertEqual(result.return_code, 0, "List PuppetModule - retcode")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
