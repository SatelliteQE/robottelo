# -*- encoding: utf-8 -*-
"""Test class for Smart Class Parameter CLI."""

from robottelo import ssh
from robottelo.cli.smartclass import SmartClassParameter
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


# pylint: disable=no-self-use
@run_only_on('sat')
class TestSmartClassParameter(CLITestCase):
    """Test class for Smart Class Parameter CLI."""

    def run_puppet_module(self):
        """Import some parameterized puppet class. This is required to make
        sure that we have smart class variable available.

        """
        ssh.command('puppet module install --force puppetlabs/ntp')

    def test_bugzilla_1047794(self):
        """@Test: Check if SmartClass Paramter Info generates an error

        @Feature: SmartClass Paramter - Info

        @Assert: SmartClass Paramter Info does not generate an error

        """
        self.run_puppet_module()
        SmartClassParameter.list()
