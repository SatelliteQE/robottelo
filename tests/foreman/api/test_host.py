# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain  CLI
"""
from baseapi import BaseAPI

from robottelo.api.apicrud import ApiCrud
from robottelo.records.host import Host


class TestHost(BaseAPI):

    def test_create(self):
        """
        @feature: Hosts
        @test: Create host, with all of its dependencies
        @assert: a valid host is created
        """

        h = Host()
        h_cr = ApiCrud.record_create_recursive(h)
        self.assertTrue(h.name == h_cr.name)

    def test_remove(self):
        """
        @feature: Hosts
        @test: Verify, that remove funkcionality works as intended
        @assert: host didn't exist, after create does, after remove doesn't
        """
        h = Host()
        self.assertTrue(ApiCrud.record_exists(h) is False)
        ApiCrud.record_create_recursive(h)
        self.assertTrue(ApiCrud.record_exists(h) is True)
        ApiCrud.record_remove(h)
        self.assertTrue(ApiCrud.record_exists(h) is False)

    def test_recursive_resolve(self):
        """
        @feature: Hosts
        @test: Verify, that we can get information about related fields
        @assert: host's defined operating system is correctly assigned
        """
        h = Host()
        h_cr = ApiCrud.record_create_recursive(h)
        h_rr = ApiCrud.record_resolve_recursive(h_cr)
        self.assertTrue(h.operatingsystem.name == h_rr.operatingsystem.name)
