#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.cli.host import Host
from lib.common.helpers import generate_name
from lib.common.helpers import generate_mac

import unittest


class TestHost(BaseCLI):

    @unittest.skip("Test needs to create required objects.")
    def test_create_host(self, delimiter=":"):
        mac_addr = generate_mac(delimiter)
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
            "mac": mac_addr
        }
        Host().create(args)
