# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host CLI
"""

from robottelo.cli.host import Host
from tests.foreman.cli.basecli import BaseCLI
from robottelo.records.host import Host as HostRecord
from robottelo.api.apicrud import ApiCrud as Api


#import sys
#if sys.hexversion >= 0x2070000:
#    import unittest
#else:
#    import unittest2 as unittes


class TestHost(BaseCLI):

    def test_create_host(self):
        """
        @Feature: Host - Positive Create
        @Test: Check if host can be created
        @Assert: Host is created
        """
        # Change delimiter to whatever you want, of course
        # in other tests
        host = Api.record_create_dependencies(HostRecord())

        "Create new host"
        # TODO need to create env, architecture, domain etc.
        args = {
            "name": host.name,
            "environment-id": host.environment_id,
            "architecture-id": host.architecture_id,
            "domain-id":  host.domain_id,
            "puppet-proxy-id": host.puppet_proxy_id,
            "operatingsystem-id": host.operatingsystem_id,
            "partition-table-id": host.ptable_id,
            "root-password": host.root_pass,
            "mac":  host.mac
        }
        r = Host().create(args)
        self.assertEqual(r.return_code, 0)
        self.assertEqual(r.stdout['name'], host.name)
