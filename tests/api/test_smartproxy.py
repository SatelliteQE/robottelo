# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import unittest

from ddt import data, ddt
from robottelo.common.constants import NOT_IMPLEMENTED
from tests.api.baseapi import BaseAPI


@ddt
class TestSmartproxy(BaseAPI):
    """Testing /api/organization entrypoint"""

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

        pass
