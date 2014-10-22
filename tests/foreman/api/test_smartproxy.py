"""Tests for the ``smart_proxies`` paths."""
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import run_only_on
import unittest
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
class SmartProxyTestCaseStub(unittest.TestCase):
    """Incomplete tests for smart proxies.

    When implemented, each of these tests should probably be data-driven. A
    decorator of this form might be used::

        @data(
            medium name is alpha,
            medium name is alpha_numeric,
            medium name is html,
            medium name is latin1,
            medium name is numeric,
            medium name is utf-8,
        )

    """
    _multiprocess_can_split_ = True

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """
