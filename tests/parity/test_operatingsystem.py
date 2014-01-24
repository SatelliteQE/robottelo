# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for OperatingSystems
"""

from basecommon import BaseCommon
from robottelo.cli.records.clicrud import CliCrud
from robottelo.api.apicrud import ApiCrud
from robottelo.common.records.operatingsystems import OperatingSystems

class TestOperatingsystem(BaseCommon):

    def test_create_api_read_cli(self):
        d = OperatingSystems()
        d_api = ApiCrud.record_create(d)
        d_cli = CliCrud.record_resolve(d_api)
        print d_cli.name == "{0} {1}.{2}".format(d_api.name,d_api.major,d_api.minor)

    def test_create_cli_read_api(self):
        d = OperatingSystems()
        d_cli = CliCrud.record_create(d)
        d_api = ApiCrud.record_resolve(d)
        print d.name == d_api.name

