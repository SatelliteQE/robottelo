# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import data
from tests.foreman.api.baseapi import APITestCase


@ddt
class TestComputeresource(APITestCase):
    """Testing /api/organization entrypoint"""

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_computeresource_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource name
        @assert: computeresource is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_computeresource_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        ID and computeresource name
        @assert: computeresource is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_computeresource_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource ID
        @assert: computeresource is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_computeresource_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        ID and computeresource ID
        @assert: computeresource is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_computeresource_1(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource name
        @assert: computeresource is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_computeresource_2(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        ID and computeresource name
        @assert: computeresource is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_computeresource_3(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource ID
        @assert: computeresource is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_computeresource_4(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        ID and computeresource ID
        @assert: computeresource is added
        @status: manual
        """

        pass
