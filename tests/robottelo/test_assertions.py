"""Tests for custom assertions in ``robottelo.test.TestCase``."""
from collections import namedtuple

import pytest
from requests import HTTPError

from robottelo.cli.base import CLIReturnCodeError
from robottelo.test import APITestCase


def fake_128_return_code():
    """Fake CLI response with 128 return_code"""
    # flake8:noqa (line-too-long)
    raise CLIReturnCodeError(
        128,
        """[ERROR 2017-03-01 05:58:50 API] 404 Resource Not Found
        [ERROR 2017-03-01 05:58:50 Exception] Resource medium not found by id \\'1\\'
        Resource medium not found by id \\'1\\'
        [ERROR 2017-03-01 05:58:50 Exception]

        RestClient::ResourceNotFound (404 Resource Not Found):""",
        """Command "medium info" finished with return_code 128
        stderr contains following message:
        [ERROR 2017-03-01 05:58:50 API] 404 Resource Not Found
        [ERROR 2017-03-01 05:58:50 Exception] Resource medium not found by id \\'1\\'
        Resource medium not found by id \\'1\\'
        [ERROR 2017-03-01 05:58:50 Exception]

        RestClient::ResourceNotFound (404 Resource Not Found):""",
    )


def fake_404_response():
    """Fake HTTP response with 404 status code"""
    response = namedtuple('response', 'ok raw reason request status_code')
    response.status_code = 404
    raise HTTPError(
        '404 Client Error: Not Found for url: https://example.com/api/v2/hosts/1',
        response=response,
    )


def fake_200_response():
    """Fake HTTP response with 200 status code"""
    response = namedtuple('response', 'ok raw reason request status_code')
    response.status_code = 200
    return response


class APIAssertNotRaisesTestCase(APITestCase):
    """Generic and API specific tests for
    :meth:`robottelo.test.TestCase.assertNotRaises`.
    """

    @classmethod
    def setUpClass(cls):
        """Do not inherit and stub :meth:`setUpClass`."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Do not inherit and stub :meth:`tearDownClass`."""
        pass

    def setUp(self):
        """Do not inherit and stub :meth:`setUp`."""
        pass

    def tearDown(self):
        """Do not inherit and stub :meth:`tearDown`."""
        pass

    def _set_worker_logger(self, worker_id):
        """Do not inherit and stub ``_get_worker_logger`` not to have to deal
        with worker ids and logger.
        """
        pass

    def test_positive_raised_callable(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(AssertionError):
            self.assertNotRaises(HTTPError, fake_404_response)

    def test_positive_raised_context_manager(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(AssertionError):
            with self.assertNotRaises(HTTPError):
                fake_404_response()

    def test_positive_raised_callable_with_status_code(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception with expected http_status_code was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(AssertionError):
            self.assertNotRaises(HTTPError, fake_404_response, expected_value=404)

    def test_positive_raised_context_manager_with_status_code(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception with expected http_status_code was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(AssertionError):
            with self.assertNotRaises(HTTPError, expected_value=404):
                fake_404_response()

    def test_positive_not_raised_callable(self):
        """Assert that the test won't fail in case exception was not risen
        inside :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        self.assertNotRaises(HTTPError, fake_200_response)

    def test_positive_not_raised_context_manager(self):
        """Assert that the test won't fail in case exception was not risen
        inside :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with self.assertNotRaises(HTTPError):
            fake_200_response()

    def test_negative_wrong_exception_raised_callable(self):
        """Assert that unexpected exception won't be handled and passed through
        to the test from :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(ZeroDivisionError):
            self.assertNotRaises(HTTPError, 1 / 0)

    def test_negative_wrong_exception_raised_context_manager(self):
        """Assert that unexpected exception won't be handled and passed through
        to the test from :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(ValueError):
            with self.assertNotRaises(HTTPError):
                raise ValueError

    def test_negative_wrong_status_code_callable(self):
        """Assert that expected exception with unexpected http_status_code
        won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaises(HTTPError, fake_404_response, expected_value=405)

    def test_negative_wrong_status_code_context_manager(self):
        """Assert that expected exception with unexpected http_status_code
        won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaises(HTTPError, expected_value=405):
                fake_404_response()

    def test_negative_wrong_exception_and_status_code_callable(self):
        """Assert that unexpected exception with unexpected status code won't
        be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaises(ZeroDivisionError, fake_404_response, expected_value=405)

    def test_negative_wrong_exception_and_status_code_context_manager(self):
        """Assert that unexpected exception with unexpected status code won't
        be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaises(ZeroDivisionError, expected_value=405):
                fake_404_response()

    def test_negative_wrong_exception_correct_status_code_callable(self):
        """Assert that unexpected exception with expected status code won't be
        handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaises(ZeroDivisionError, fake_404_response, expected_value=404)

    def test_negative_wrong_exc_correct_status_code_context_manager(self):
        """Assert that unexpected exception with expected status code won't be
        handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaises` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaises(ZeroDivisionError, expected_value=404):
                fake_404_response()


class APIAssertNotRaisesRegexTestCase(APITestCase):
    """Generic and API specific tests for
    :meth:`robottelo.test.TestCase.assertNotRaisesRegex`.
    """

    @classmethod
    def setUpClass(cls):
        """Do not inherit and stub :meth:`setUpClass`."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Do not inherit and stub :meth:`tearDownClass`."""
        pass

    def setUp(self):
        """Do not inherit and stub :meth:`setUp`."""
        pass

    def tearDown(self):
        """Do not inherit and stub :meth:`tearDown`."""
        pass

    def _set_worker_logger(self, worker_id):
        """Do not inherit and stub ``_get_worker_logger`` not to have to deal
        with worker ids and logger.
        """
        pass

    pattern = '404 Client Error'

    def test_positive_raised_callable(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call and expected
        pattern was found in exception message.
        """
        with pytest.raises(AssertionError):
            self.assertNotRaisesRegex(HTTPError, self.pattern, fake_404_response)

    def test_positive_raised_context_manager(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block and expected
        pattern was found in exception message.
        """
        with pytest.raises(AssertionError):
            with self.assertNotRaisesRegex(HTTPError, self.pattern):
                fake_404_response()

    def test_positive_raised_callable_with_status_code(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call and
        http_status_code altogether with regex pattern match expected ones.
        """
        with pytest.raises(AssertionError):
            self.assertNotRaisesRegex(
                HTTPError, self.pattern, fake_404_response, expected_value=404
            )

    def test_positive_raised_context_manager_with_status_code(self):
        """Assert that the test will fail (not marked as errored) in case
        expected exception was risen inside
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block and
        http_status_code altogether with regex pattern match expected ones.
        """
        with pytest.raises(AssertionError):
            with self.assertNotRaisesRegex(HTTPError, self.pattern, expected_value=404):
                fake_404_response()

    def test_positive_not_raised_callable(self):
        """Assert that the test won't fail in case exception was not risen
        inside :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        self.assertNotRaisesRegex(HTTPError, self.pattern, fake_200_response)

    def test_positive_not_raised_context_manager(self):
        """Assert that the test won't fail in case exception was not risen
        inside :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with self.assertNotRaisesRegex(HTTPError, self.pattern):
            fake_200_response()

    def test_negative_wrong_exception_raised_callable(self):
        """Assert that unexpected exception with expected pattern won't be
        handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(ZeroDivisionError):
            self.assertNotRaisesRegex(HTTPError, self.pattern, 1 / 0)

    def test_negative_wrong_exception_raised_context_manager(self):
        """Assert that unexpected exception with expected pattern won't be
        handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(ValueError):
            with self.assertNotRaisesRegex(HTTPError, self.pattern):
                raise ValueError

    def test_negative_wrong_status_code_callable(self):
        """Assert that expected exception with valid pattern but unexpected
        http_status_code won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(
                HTTPError, self.pattern, fake_404_response, expected_value=405
            )

    def test_negative_wrong_status_code_context_manager(self):
        """Assert that expected exception with valid pattern but unexpected
        http_status_code won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(HTTPError, self.pattern, expected_value=405):
                fake_404_response()

    def test_negative_wrong_exception_and_status_code_callable(self):
        """Assert that unexpected exception with unexpected status code but
        expected pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(
                ZeroDivisionError, self.pattern, fake_404_response, expected_value=405
            )

    def test_negative_wrong_exception_and_status_code_context_manager(self):
        """Assert that unexpected exception with unexpected status code but
        expected pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(ZeroDivisionError, self.pattern, expected_value=405):
                fake_404_response()

    def test_negative_wrong_exception_correct_status_code_callable(self):
        """Assert that unexpected exception with expected status code and
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(
                ZeroDivisionError, self.pattern, fake_404_response, expected_value=404
            )

    def test_negative_wrong_exc_correct_status_code_context_manager(self):
        """Assert that unexpected exception with expected status code and
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(ZeroDivisionError, self.pattern, expected_value=404):
                fake_404_response()

    def test_negative_wrong_pattern_correct_exc_status_code_callable(self):
        """Assert that expected exception with expected status code but invalid
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(HTTPError, 'foo', fake_404_response, expected_value=404)

    def test_negative_wrong_pattern_correct_exc_status_context_manager(self):
        """Assert that expected exception with expected status code but invalid
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(HTTPError, 'foo', expected_value=404):
                fake_404_response()

    def test_negative_wrong_pattern_status_code_correct_exc_callable(self):
        """Assert that expected exception with unexpected status code and
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(HTTPError, 'foo', fake_404_response, expected_value=405)

    def test_negative_wrong_pattern_status_code_correct_exc_manager(self):
        """Assert that expected exception with unexpected status code and
        pattern won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` block.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(HTTPError, 'foo', expected_value=405):
                fake_404_response()

    def test_negative_wrong_pattern_exc_correct_status_code_callable(self):
        """Assert that unexpected exception with invalid patter but expected
        status code won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            self.assertNotRaisesRegex(
                ZeroDivisionError, 'foo', fake_404_response, expected_value=404
            )

    def test_negative_wrong_pattern_exc_correct_status_code_manager(self):
        """Assert that unexpected exception with invalid patter but expected
        status code won't be handled and passed through to the test from
        :meth:`robottelo.test.TestCase.assertNotRaisesRegex` call.
        """
        with pytest.raises(HTTPError):
            with self.assertNotRaisesRegex(ZeroDivisionError, 'foo', expected_value=404):
                fake_404_response()
