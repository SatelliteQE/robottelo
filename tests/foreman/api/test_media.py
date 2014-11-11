"""Tests for the ``media`` paths."""
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import run_only_on
import unittest
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
class MediaTestCase(unittest.TestCase):
    """Incomplete tests for media.

    When implemented, each of these tests should probably be data-driven. A
    decorator of this form might be used::

        @data(
            name is alpha,
            name is alpha_numeric,
            name is html,
            name is latin1,
            name is numeric,
            name is utf-8,
        )

    """
    _multiprocess_can_split_ = True

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_medium_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium name
        @assert: medium is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_medium_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization ID and medium name
        @assert: medium is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_medium_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium ID
        @assert: medium is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_remove_medium_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization ID and medium ID
        @assert: medium is added then removed
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_medium_1(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium name
        @assert: medium is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_medium_2(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization ID and medium name
        @assert: medium is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_medium_3(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium ID
        @assert: medium is added
        @status: manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_add_medium_4(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization ID and medium ID
        @assert: medium is added
        @status: manual
        """
