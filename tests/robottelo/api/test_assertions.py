# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from requests import HTTPError

from robottelo.api.assertions import assert_api_not_raises
from robottelo.api.assertions import assert_api_not_raises_regex
from tests.robottelo.test_assertions import fake_200_response
from tests.robottelo.test_assertions import fake_404_response


def test_positive_raised_callable():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(AssertionError):
        assert_api_not_raises(HTTPError, fake_404_response)


def test_positive_raised_context_manager():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(AssertionError):
        with assert_api_not_raises(HTTPError):
            fake_404_response()


def test_positive_raised_callable_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception with expected http_status_code was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(AssertionError):
        assert_api_not_raises(HTTPError, fake_404_response, expected_value=404)


def test_positive_raised_context_manager_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception with expected http_status_code was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(AssertionError):
        with assert_api_not_raises(HTTPError, expected_value=404):
            fake_404_response()


def test_positive_not_raised_callable():
    """Assert that the test won't fail in case exception was not risen
    inside :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    assert_api_not_raises(HTTPError, fake_200_response)


def test_positive_not_raised_context_manager():
    """Assert that the test won't fail in case exception was not risen
    inside :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with assert_api_not_raises(HTTPError):
        fake_200_response()


def test_negative_wrong_exception_raised_callable():
    """Assert that unexpected exception won't be handled and passed through
    to the test from :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(ZeroDivisionError):
        assert_api_not_raises(HTTPError, 1 / 0)


def test_negative_wrong_exception_raised_context_manager():
    """Assert that unexpected exception won't be handled and passed through
    to the test from :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(ValueError):
        with assert_api_not_raises(HTTPError):
            raise ValueError


def test_negative_wrong_status_code_callable():
    """Assert that expected exception with unexpected http_status_code
    won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises(HTTPError, fake_404_response, expected_value=405)


def test_negative_wrong_status_code_context_manager():
    """Assert that expected exception with unexpected http_status_code
    won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises(HTTPError, expected_value=405):
            fake_404_response()


def test_negative_wrong_exception_and_status_code_callable():
    """Assert that unexpected exception with unexpected status code won't
    be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises(ZeroDivisionError, fake_404_response, expected_value=405)


def test_negative_wrong_exception_and_status_code_context_manager():
    """Assert that unexpected exception with unexpected status code won't
    be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises(ZeroDivisionError, expected_value=405):
            fake_404_response()


def test_negative_wrong_exception_correct_status_code_callable():
    """Assert that unexpected exception with expected status code won't be
    handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises(ZeroDivisionError, fake_404_response, expected_value=404)


def test_negative_wrong_exc_correct_status_code_context_manager():
    """Assert that unexpected exception with expected status code won't be
    handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises(ZeroDivisionError, expected_value=404):
            fake_404_response()


pattern = '404 Client Error'


def test_positive_regex_raised_callable():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call and expected
    pattern was found in exception message.
    """
    with pytest.raises(AssertionError):
        assert_api_not_raises_regex(HTTPError, pattern, fake_404_response)


def test_positive_regex_raised_context_manager():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block and expected
    pattern was found in exception message.
    """
    with pytest.raises(AssertionError):
        with assert_api_not_raises_regex(HTTPError, pattern):
            fake_404_response()


def test_positive_regex_raised_callable_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call and
    http_status_code altogether with regex pattern match expected ones.
    """
    with pytest.raises(AssertionError):
        assert_api_not_raises_regex(HTTPError, pattern, fake_404_response, expected_value=404)


def test_positive_regex_raised_context_manager_with_status_code():
    """Assert that the test will fail (not marked as errored) in case
    expected exception was risen inside
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block and
    http_status_code altogether with regex pattern match expected ones.
    """
    with pytest.raises(AssertionError):
        with assert_api_not_raises_regex(HTTPError, pattern, expected_value=404):
            fake_404_response()


def test_positive_regex_not_raised_callable():
    """Assert that the test won't fail in case exception was not risen
    inside :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    assert_api_not_raises_regex(HTTPError, pattern, fake_200_response)


def test_positive_regex_not_raised_context_manager():
    """Assert that the test won't fail in case exception was not risen
    inside :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with assert_api_not_raises_regex(HTTPError, pattern):
        fake_200_response()


def test_negative_regex_wrong_exception_raised_callable():
    """Assert that unexpected exception with expected pattern won't be
    handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(ZeroDivisionError):
        assert_api_not_raises_regex(HTTPError, pattern, 1 / 0)


def test_negative_regex_wrong_exception_raised_context_manager():
    """Assert that unexpected exception with expected pattern won't be
    handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(ValueError):
        with assert_api_not_raises_regex(HTTPError, pattern):
            raise ValueError


def test_negative_regex_wrong_status_code_callable():
    """Assert that expected exception with valid pattern but unexpected
    http_status_code won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(HTTPError, pattern, fake_404_response, expected_value=405)


def test_negative_regex_wrong_status_code_context_manager():
    """Assert that expected exception with valid pattern but unexpected
    http_status_code won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(HTTPError, pattern, expected_value=405):
            fake_404_response()


def test_negative_regex_wrong_exception_and_status_code_callable():
    """Assert that unexpected exception with unexpected status code but
    expected pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(
            ZeroDivisionError, pattern, fake_404_response, expected_value=405
        )


def test_negative_regex_wrong_exception_and_status_code_context_manager():
    """Assert that unexpected exception with unexpected status code but
    expected pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(ZeroDivisionError, pattern, expected_value=405):
            fake_404_response()


def test_negative_regex_wrong_exception_correct_status_code_callable():
    """Assert that unexpected exception with expected status code and
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(
            ZeroDivisionError, pattern, fake_404_response, expected_value=404
        )


def test_negative_regex_wrong_exc_correct_status_code_context_manager():
    """Assert that unexpected exception with expected status code and
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(ZeroDivisionError, pattern, expected_value=404):
            fake_404_response()


def test_negative_regex_wrong_pattern_correct_exc_status_code_callable():
    """Assert that expected exception with expected status code but invalid
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(HTTPError, 'foo', fake_404_response, expected_value=404)


def test_negative_regex_wrong_pattern_correct_exc_status_context_manager():
    """Assert that expected exception with expected status code but invalid
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(HTTPError, 'foo', expected_value=404):
            fake_404_response()


def test_negative_regex_wrong_pattern_status_code_correct_exc_callable():
    """Assert that expected exception with unexpected status code and
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(HTTPError, 'foo', fake_404_response, expected_value=405)


def test_negative_regex_wrong_pattern_status_code_correct_exc_manager():
    """Assert that expected exception with unexpected status code and
    pattern won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` block.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(HTTPError, 'foo', expected_value=405):
            fake_404_response()


def test_negative_regex_wrong_pattern_exc_correct_status_code_callable():
    """Assert that unexpected exception with invalid patter but expected
    status code won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        assert_api_not_raises_regex(
            ZeroDivisionError, 'foo', fake_404_response, expected_value=404
        )


def test_negative_regex_wrong_pattern_exc_correct_status_code_manager():
    """Assert that unexpected exception with invalid patter but expected
    status code won't be handled and passed through to the test from
    :meth:`robottelo.api.assertions.assert_api_not_raises_regex` call.
    """
    with pytest.raises(HTTPError):
        with assert_api_not_raises_regex(ZeroDivisionError, 'foo', expected_value=404):
            fake_404_response()
