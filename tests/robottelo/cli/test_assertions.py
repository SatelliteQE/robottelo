# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from robottelo.cli.assertions import assert_cli_not_raises
from robottelo.cli.assertions import assert_cli_not_raises_regex
from robottelo.cli.base import CLIReturnCodeError
from tests.robottelo.test_assertions import fake_128_return_code


def test_positive_raised_callable_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception with expected cli_return_code code was risen inside
    a pure pytest call.
    """
    with pytest.raises(AssertionError):
        assert_cli_not_raises(
            CLIReturnCodeError, fake_128_return_code, expected_value=128)


def test_positive_raised_context_manager_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception with expected cli_return_code was risen inside
    pure pytest block.
    """
    with pytest.raises(AssertionError):
        with assert_cli_not_raises(CLIReturnCodeError, expected_value=128):
            fake_128_return_code()


def test_negative_wrong_status_code_callable():
    """Assert that expected exception with unexpected cli_return_code
    won't be handled and passed through to the test from
    pure pytest call.
    """
    with pytest.raises(CLIReturnCodeError):
        assert_cli_not_raises(
            CLIReturnCodeError, fake_128_return_code, expected_value=129)


def test_negative_wrong_status_code_context_manager():
    """Assert that expected exception with unexpected cli_return_code
    status code won't be handled and passed through to the test from
    pure pytest block.
    """
    with pytest.raises(CLIReturnCodeError):
        with assert_cli_not_raises(CLIReturnCodeError, expected_value=129):
            fake_128_return_code()


# Regex tests
pattern = '404 Resource Not Found'


def test_regex_positive_raised_callable_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    `robottelo.cli.assertions.assert_cli_not_raises_regex` call and
    cli_return_code altogether with regex pattern match expected ones.
    """
    with pytest.raises(AssertionError):
        assert_cli_not_raises_regex(
            CLIReturnCodeError, pattern, fake_128_return_code,
            expected_value=128,
        )


def test_regex_positive_raised_context_manager_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    `robottelo.cli.assertions.assert_cli_not_raises_regex` block and
    cli_return_code altogether with regex pattern match expected ones.
    """
    with pytest.raises(AssertionError):
        with assert_cli_not_raises_regex(CLIReturnCodeError, pattern,
                                         expected_value=128):
            fake_128_return_code()


def test_regex_negative_wrong_status_code_callable():
    """Assert that expected exception with valid pattern but unexpected
    cli_return_code won't be handled and passed through to the test from
    `robottelo.cli.assertions.assert_cli_not_raises_regex` call.
    """
    with pytest.raises(CLIReturnCodeError):
        assert_cli_not_raises_regex(
            CLIReturnCodeError,
            pattern,
            fake_128_return_code,
            expected_value=129,
        )


def test_regex_negative_wrong_status_code_context_manager():
    """Assert that expected exception with valid pattern but unexpected
    cli_return_code won't be handled and passed through to the test from
    `robottelo.cli.assertions.assert_cli_not_raises_regex` block.
    """
    with pytest.raises(CLIReturnCodeError):
        with assert_cli_not_raises_regex(
            CLIReturnCodeError,
            pattern,
            expected_value=129,
        ):
            fake_128_return_code()
