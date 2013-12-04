#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name
from lib.common.helpers import generate_mac


class Host(BaseCLI):

    def test_create_host(self):
        "Create new host"
        # TODO need to create env, architecture, domain etc.
        args = {
            "name": generate_name(6),
            "environment-id": 1,
            "architecture-id": 1,
            "domain-id": 1,
            "puppet-proxy-id": 1,
            "operatingsystem-id": 1,
            "partition-table-id": 1,
            "mac": generate_mac()
        }
        self.assertTrue(self.host.create(args))
