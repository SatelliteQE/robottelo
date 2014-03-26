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
from tests.api.baseapi import BaseAPI


@ddt
class TestSubnet(BaseAPI):
    """Testing /api/organization entrypoint"""

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_subnet_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet name
        @assert: subnet is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_subnet_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization ID and subnet name
        @assert: subnet is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_subnet_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet ID
        @assert: subnet is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_subnet_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization ID and subnet ID
        @assert: subnet is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_subnet_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet name
        @assert: subnet is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_subnet_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization ID and subnet name
        @assert: subnet is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_subnet_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet ID
        @assert: subnet is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_subnet_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization ID and subnet ID
        @assert: subnet is added then removed
        @status: manual
        """

        pass
