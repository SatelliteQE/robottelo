#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name


class Hostgroup(BaseCLI):

    def test_hostgroup_create(self):
        "Create new hostgroup"
        name = generate_name()
        res = self.hostgroup.create(name)
        self.assertTrue(res)
