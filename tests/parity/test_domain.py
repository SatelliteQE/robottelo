# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain  CLI
"""
from basecommon import BaseCommon

from robottelo.cli.records.clicrud import CliCrud
from robottelo.api.apicrud import ApiCrud
from robottelo.common.records.domains import Domains


class TestDomain(BaseCommon):

    def test_create_api_read_cli(self):
        """Create a new domain"""
        d = Domains()
        d_api = ApiCrud.record_create(d)
        d_cli = CliCrud.record_resolve(d_api)
        self.assertTrue(d_api.name ==  d_cli.name)

    def test_create_cli_read_api(self):
        """Create a new domain"""
        d = Domains()
        d_cli = CliCrud.record_create(d)
        d_api = ApiCrud.record_resolve(d_cli)
        self.assertTrue(d_api.name ==  d_cli.name)
