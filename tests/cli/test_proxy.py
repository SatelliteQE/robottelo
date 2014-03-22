# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Smart proxy CLI
"""

from tests.cli.basecli import BaseCLI
from robottelo.cli.factory import make_proxy
#from robottelo.cli.proxy import Proxy
from robottelo.common.decorators import redminebug


class TestProxy(BaseCLI):

    @redminebug('3875')
    def test_redmine_3875(self):
        """
        @Test: Proxy creation with random URL
        @Feature: Smart Proxy
        @Assert: Proxy is not created
        """

        # Create a random proxy
        with self.assertRaises(Exception):
            make_proxy()
