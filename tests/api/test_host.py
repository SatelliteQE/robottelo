# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain  CLI
"""
from baseapi import BaseApi
from positive_crud_tests import PositiveCrudTest

from robottelo.api.apicrud import ApiCrud
from robottelo.records import Host


class TestHost(BaseApi):

    def test_create(self):
        h = Host()
        h_cr = ApiCrud.record_create_recursive(h)
        self.assertTrue(h.name ==  h_cr.name)

    def test_remove(self):
        h = Host()
        self.assertTrue(ApiCrud.record_exists(h)==False)
        h_cr = ApiCrud.record_create_recursive(h)
        self.assertTrue(ApiCrud.record_exists(h)==True)
        h_cr = ApiCrud.record_remove(h)
        self.assertTrue(ApiCrud.record_exists(h)==False)

    def test_recursive_resolve(self):
        h = Host()
        h_cr = ApiCrud.record_create_recursive(h)
        h_rr = ApiCrud.record_resolve_recursive(h_cr)
        self.assertTrue(h.operatingsystem.name==h_rr.operatingsystem.name)
