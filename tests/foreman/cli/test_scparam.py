# -*- encoding: utf-8 -*-
"""Test class for Smart Class Parameter CLI."""

from robottelo import ssh
from robottelo.cli.smartclass import SmartClassParameter
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


# pylint: disable=no-self-use
class SmartClassParameterTestCase(CLITestCase):
    """Test class for Smart Class Parameter CLI."""

    def run_puppet_module(self):
        """Import some parameterized puppet class. This is required to make
        sure that we have smart class variable available.

        """
        ssh.command('puppet module install --force puppetlabs/ntp')

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """Check if SmartClass Paramter ``list`` generates an error

        @Feature: SmartClass Paramter

        @Assert: SmartClass Paramter ``list`` does not generate an error

        """
        self.run_puppet_module()
        SmartClassParameter.list()
