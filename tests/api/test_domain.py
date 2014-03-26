# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import sys
if sys.hexversion >= 0x2070000:
	import unittest
else:
	import unittest2
	unittest=unittest2

from ddt import data, ddt
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import redminebug
from tests.api.baseapi import BaseAPI


@ddt
class TestDomain(BaseAPI):
    """Testing /api/organization entrypoint"""

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_domain_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization
        @assert: Domain is added to organization
        @status: manual
        """

        pass

    # Associations

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_domain_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain name
        @assert: the domain is removed from the organization
        @status: manual
        """

        pass

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_domain_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        ID and domain name
        @assert: the domain is removed from the organization
        @status: manual
        """

        pass

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_domain_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain ID
        @assert: the domain is removed from the organization
        @status: manual
        """

        pass

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_domain_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        ID and domain ID
        @assert: the domain is removed from the organization
        @status: manual
        """

        pass
