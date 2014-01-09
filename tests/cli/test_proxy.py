# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Smart proxy CLI
"""

import unittest

from basecli import BaseCLI
from robottelo.cli.factory import make_proxy
from robottelo.cli.proxy import Proxy


class TestProxy(BaseCLI):

    @unittest.skip("skipped due to http://projects.theforeman.org/issues/3875")
    def test_create_proxy(self):
        """Create a new proxy"""

        result = make_proxy()
        proxy = Proxy().info({'name': result['name']})
        self.assertEqual(result['name'], proxy.stdout['name'])
