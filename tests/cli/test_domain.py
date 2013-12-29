# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain  CLI
"""

from basecli import BaseCLI
from robottelo.cli.domain import Domain
from robottelo.common.helpers import generate_name


class TestDomain(BaseCLI):

    def test_create_domain(self):
        """Create a new domain"""
        args = {
            "name": generate_name(6)
        }

        Domain().create(args)
        self.assertTrue(Domain().exists(('name', args['name'])))
