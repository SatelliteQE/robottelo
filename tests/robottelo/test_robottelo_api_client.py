"""Unit tests for module ``robottelo.api.client``."""
from robottelo.api import client
from unittest import TestCase
from urllib import urlencode


# (accessing private members) pylint: disable=W0212
# (too many public methods) pylint: disable=R0904


# Start mock definitions ------------------------------------------------------


class MockRequest(object):  # (too few methods) pylint: disable=R0903
    """A mock ``requests.request`` function."""
    def __init__(self, method, url, **kwargs):
        # The loggers read this data.
        self.status_code = 0
        self.content = ''
        # The tests look for this data.
        self.method = method
        self.url = url
        self.kwargs = kwargs


class MockHeadGetDelete(object):  # (too few methods) pylint: disable=R0903
    """
    A mock ``requests.head``, ``requests.get`` or ``requests.delete`` function.
    """
    def __init__(self, url, **kwargs):
        # The loggers read this data.
        self.status_code = 0
        self.content = ''
        # The tests look for this data.
        self.url = url
        self.kwargs = kwargs


class MockPostPutPatch(object):  # (too few methods) pylint: disable=R0903
    """
    A mock ``requests.post``, ``requests.put`` or ``requests.patch`` function.
    """
    def __init__(self, url, data=None, **kwargs):
        # The loggers read this data.
        self.status_code = 0
        self.content = ''
        # The tests look for this data.
        self.url = url
        self.data = data
        self.kwargs = kwargs


# Start test case definitions -------------------------------------------------


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
        client._call_requests_request = MockRequest

    def test_null(self):
        """Do not provide any optional args."""
        self.assertTrue(isinstance(
            client.request('GET', 'example.com'),
            MockRequest,
        ))

    def test_non_null(self):
        """Provide optional args. Ensure they are given to wrapped function."""
        kwargs = {'foo': 2, 'verify': False}
        response = client.request('GET', 'example.com', **kwargs)  # flake8:noqa pylint:disable=W0142
        self.assertTrue(isinstance(response, MockRequest))
        self.assertEqual(response.method, 'GET')
        self.assertEqual(response.url, 'example.com')
        self.assertEqual(response.kwargs, kwargs)


class HeadGetDeleteTestCase(TestCase):
    """Tests for functions ``head``, ``get`` and ``delete``."""
    def setUp(self):  # pylint: disable=C0103
        """Override calls to real ``requests`` functions."""
        client._call_requests_head = MockHeadGetDelete
        client._call_requests_get = MockHeadGetDelete
        client._call_requests_delete = MockHeadGetDelete

    def test_null(self):
        """Do not provide any optional args."""
        for function in (client.head, client.get, client.delete):
            self.assertTrue(isinstance(
                function('example.com'),
                MockHeadGetDelete,
            ))

    def test_non_null(self):
        """Provide optional args. Ensure they are given to wrapped function."""
        kwargs = {'foo': 2, 'verify': False}
        for function in (client.head, client.get, client.delete):
            response = function('example.com', **kwargs)  # flake8:noqa pylint:disable=W0142
            self.assertTrue(isinstance(response, MockHeadGetDelete))
            self.assertEqual(response.url, 'example.com')
            self.assertEqual(response.kwargs, kwargs)


class PostPutPatchTestCase(TestCase):
    """Tests for functions ``post``, ``put`` and ``patch``."""
    def setUp(self):  # pylint: disable=C0103
        """Override calls to real ``requests`` functions."""
        client._call_requests_post = MockPostPutPatch
        client._call_requests_put = MockPostPutPatch
        client._call_requests_patch = MockPostPutPatch

    def test_null(self):
        """Do not provide any optional args."""
        for function in (client.post, client.put, client.patch):
            self.assertTrue(isinstance(
                function('example.com'),
                MockPostPutPatch,
            ))

    def test_non_null(self):
        """Provide optional args. Ensure they are given to wrapped function."""
        data = 'arbitrary value'
        kwargs = {'foo': 2, 'verify': False}
        for function in (client.post, client.put, client.patch):
            response = function('example.com', data=data, **kwargs)  # flake8:noqa pylint:disable=W0142
            self.assertTrue(isinstance(response, MockPostPutPatch))
            self.assertEqual(response.url, 'example.com')
            self.assertEqual(response.kwargs, kwargs)
