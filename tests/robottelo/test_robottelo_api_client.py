"""Unit tests for module ``robottelo.api.client``."""
from robottelo.api import client
from unittest import TestCase
from urllib import urlencode


# (accessing private members) pylint: disable=W0212
# (too many public methods) pylint: disable=R0904


class CurlArgUserTestCase(TestCase):
    """Tests for function ``_curl_arg_user``."""
    def test_null(self):
        """Do not provide any authentication information."""
        self.assertEqual(client._curl_arg_user({}), '')

    def test_non_null(self):
        """Provide authentication information."""
        self.assertEqual(
            client._curl_arg_user({
                'auth': ('alice', 'hackme')
            }),
            '--user alice:hackme ',  # there should be trailing whitespace
        )


class CurlArgInsecureTestCase(TestCase):
    """Tests for function ``_curl_arg_insecure``."""
    def test_null(self):
        """Do not specify whether SSL connections should be verified."""
        self.assertEqual(client._curl_arg_insecure({}), '')

    def test_positive(self):
        """Ask for SSL connections to be verified."""
        self.assertEqual(
            client._curl_arg_insecure({'verify': True}),
            '',
        )

    def test_negative(self):
        """Ask for SSL connections to not be verified."""
        self.assertEqual(
            client._curl_arg_insecure({'verify': False}),
            '--insecure ',  # there should be trailing whitespace
        )


class CurlArgDataTestCase(TestCase):
    """Tests for function ``_curl_arg_data``."""
    def setUp(self):  # pylint: disable=C0103
        """Provide test data for use by other methods in this class."""
        self.to_encode = {'foo': 9001, 'bar': '!@#$% ^&*()'}
        self.to_ignore = {'auth': ('alice', 'password'), 'verify': True}

    def test_null(self):
        """Do not provide any data to be encoded."""
        self.assertEqual(
            client._curl_arg_data({}),
            urlencode({}),
        )

    def test_ignored_opts(self):
        """Provide data which should be ignored."""
        self.assertEqual(
            client._curl_arg_data(self.to_ignore),
            urlencode({}),
        )

    def test_valid_opts(self):
        """Provide data which should be encoded."""
        self.assertEqual(
            client._curl_arg_data(self.to_encode),
            urlencode(self.to_encode),
        )

    def test_both_opts(self):
        """Provide data which should be ignored and which should be encoded."""
        self.assertEqual(
            client._curl_arg_data(dict(
                self.to_encode.items() + self.to_ignore.items()
            )),
            urlencode(self.to_encode),
        )


class RequestTestCase(TestCase):
    """Tests for function ``request``."""
    def setUp(self):  # pylint: disable=C0103
        """Override function ``_call_requests_request``."""
        class MockRequest(object):  # (too few methods) pylint: disable=R0903
            """A mock ``requests.request`` class."""
            def __init__(self, method, url, **kwargs):
                # (unused args) pylint: disable=W0613
                self.status_code = 0
                self.content = ''
        client._call_requests_request = MockRequest
        self.mock_class = MockRequest

    def test_null(self):
        """Do not provide any kwargs."""
        self.assertTrue(isinstance(
            client.request('GET', 'localhost'),
            self.mock_class,
        ))

    def test_non_null(self):
        """Provide kwargs."""
        self.assertTrue(isinstance(
            client.request('GET', 'localhost', foo=2, verify=False),
            self.mock_class,
        ))
