# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from robottelo.api.apicrud import ApiCrud, ApiException
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string
from robottelo.records.environment import Environment
from tests.foreman.api.baseapi import APITestCase


@ddt
class TestEnvironment(APITestCase):
    """Testing /api/environment entrypoint"""

    @data(
        generate_string('alpha', 8),
        generate_string('numeric', 8),
        generate_string('alphanumeric', 255),
    )
    def test_positive_create(self, name):
        """
        @Feature: Environment - Positive Create
        @Test: Create new environment
        @Assert: Environment is created
        """

        environment = Environment(name=name)
        result = ApiCrud.record_create(environment)
        self.assertEqual(result.name, environment.name)
        self.assertTrue(ApiCrud.record_exists(environment))

    @data(
        generate_string('alpha', 256),
        generate_string('numeric', 256),
        generate_string('alphanumeric', 256),
        generate_string('utf8', 8),
        generate_string('latin1', 8),
        generate_string('html', 8),
    )
    def test_negative_create(self, name):
        """
        @Feature: Environment - Negative Create
        @Test: Create new environment
        @Assert: Environment is created
        """

        environment = Environment(name=name)
        with self.assertRaises(ApiException):
            result = ApiCrud.record_create(environment)
            self.assertIsNone(result)
        self.assertFalse(ApiCrud.record_exists(environment))

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
