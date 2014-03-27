# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import data, ddt
from robottelo.common.constants import NOT_IMPLEMENTED
from tests.api.baseapi import BaseAPI


@ddt
class TestEnvironment(BaseAPI):
    """Testing /api/organization entrypoint"""

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_environment_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization name and
        evironment name
        @assert: environment is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_environment_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization ID and
        evironment name
        @assert: environment is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_environment_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization name and
        evironment ID
        @assert: environment is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_environment_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization ID and
        evironment ID
        @assert: environment is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_environment_1(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization name and evironment name
        @assert: environment is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_environment_2(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization ID and evironment name
        @assert: environment is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_environment_3(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization name and evironment ID
        @assert: environment is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_environment_4(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization ID and evironment ID
        @assert: environment is added
        @status: manual
        """

        pass
