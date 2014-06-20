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
class TestConfigtemplate(APITestCase):
    """Testing /api/organization entrypoint"""

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove config template
        @assert: configtemplate is added then removed
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_configtemplate_2(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_configtemplate_3(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_configtemplate_4(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        pass
