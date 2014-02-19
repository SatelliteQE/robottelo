# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Smart proxy CLI
"""

from tests.cli.basecli import BaseCLI
from robottelo.cli.factory import make_proxy
from robottelo.cli.proxy import Proxy
from robottelo.common.decorators import redminebug


class TestProxy(BaseCLI):

    @redminebug('3875')
    def test_create_proxy(self):
        """
        @Feature: Proxy - Create
        @Test: Check if Proxy can be created
        @Assert: Proxy is created
        """

        result = make_proxy()
        proxy = Proxy().info({'name': result['name']})
        self.assertEqual(result['name'], proxy.stdout['name'])
