#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.cli.hostgroup import HostGroup
from lib.common.helpers import generate_name


class TestHostGroup(BaseCLI):

    def test_hostgroup_create(self):
        "Create new hostgroup"

        args = {
            'name': generate_name(),
        }

        HostGroup().create(args)
        self.assertTrue(HostGroup().exists(args['name']))
