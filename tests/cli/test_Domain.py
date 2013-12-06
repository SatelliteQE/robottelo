#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name


class Domain(BaseCLI):

    def test_create_domain(self):
        """Create a new domain"""
        args = {
            "name": generate_name(6)
        }

        self.domain.create(args)
        self.assertTrue(self.domain.exists(args['name']))
