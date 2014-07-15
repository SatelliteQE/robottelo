"""Unit tests for module ``robottelo.api.client``."""
from robottelo.api import client
from unittest import TestCase
from urllib import urlencode
import ddt
import inspect
import requests


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


@ddt.ddt
class ContentTypeIsJsonTestCase(TestCase):
    """Tests for function ``_content_type_is_json``."""
    def test_true(self):
        """Ensure function returns ``True`` when appropriate."""
        mock_kwargs = {'headers': {'content-type': 'appLICatiON/JSoN'}}
        self.assertTrue(client._content_type_is_json(mock_kwargs))

    @ddt.data(
        {'headers': {'content-type': 'application-json'}},
        {'headers': {'content-type': ''}},
    )
    def test_false(self, mock_kwargs):
        """Ensure function returns ``False`` when given ``mock_kwargs``."""
        self.assertFalse(client._content_type_is_json(mock_kwargs))


class SetContentTypeTestCase(TestCase):
    """Tests for function ``_set_content_type``."""
    def test_no_value(self):
        """Ensure 'content-type' is set if no existing value is provided."""
        mock_kwargs = {'headers': {}}
        client._set_content_type(mock_kwargs)
        self.assertEqual(
            mock_kwargs,
            {'headers': {'content-type': 'application/json'}},
        )

    def test_existing_value(self):
        """Ensure 'content-type' is not set if a value is provided."""
        mock_kwargs = {'headers': {'content-type': ''}}
        client._set_content_type(mock_kwargs)
        self.assertEqual(mock_kwargs, {'headers': {'content-type': ''}})


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
    """Tests for :func:`robottelo.api.client.request`."""
    def setUp(self):  # pylint: disable=C0103
        """Backup and override ``client._call_requests_request``."""
        self._call_requests_request = client._call_requests_request
        client._call_requests_request = MockRequest

    def tearDown(self):  # pylint: disable=C0103
        """Restore ``client._call_requests_request``."""
        client._call_requests_request = self._call_requests_request

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
        for key, val in kwargs.items():
            self.assertIn(key, response.kwargs.keys())
            self.assertEqual(val, response.kwargs[key])


@ddt.ddt
class HeadGetDeleteTestCase(TestCase):
    """
    Tests for :func:`robottelo.api.client.head`,
    :func:`robottelo.api.client.get` and :func:`robottelo.api.client.delete`.
    """
    def setUp(self):  # pylint: disable=C0103
        """Backup and override several objects."""
        self._call_requests_head = client._call_requests_head
        self._call_requests_get = client._call_requests_get
        self._call_requests_delete = client._call_requests_delete
        client._call_requests_head = MockHeadGetDelete
        client._call_requests_get = MockHeadGetDelete
        client._call_requests_delete = MockHeadGetDelete

    def tearDown(self):  # pylint: disable=C0103
        """Restore backed-up objects."""
        client._call_requests_head = self._call_requests_head
        client._call_requests_get = self._call_requests_get
        client._call_requests_delete = self._call_requests_delete

    @ddt.data(
        client.delete,
        client.get,
        client.head,
    )
    def test_null(self, function):
        """Do not provide any optional args."""
        self.assertTrue(isinstance(function('example.com'), MockHeadGetDelete))

    @ddt.data(
        client.delete,
        client.get,
        client.head,
    )
    def test_non_null(self, function):
        """Provide optional args. Ensure they are given to wrapped function."""
        kwargs = {'foo': 2, 'verify': False}
        response = function('example.com', **kwargs)  # flake8:noqa pylint:disable=W0142
        self.assertTrue(isinstance(response, MockHeadGetDelete))
        self.assertEqual(response.url, 'example.com')
        for key, val in kwargs.items():
            self.assertIn(key, response.kwargs.keys())
            self.assertEqual(val, response.kwargs[key])


@ddt.ddt
class PostPutPatchTestCase(TestCase):
    """
    Tests for :func:`robottelo.api.client.post`,
    :func:`robottelo.api.client.put` and :func:`robottelo.api.client.patch`.
    """
    def setUp(self):  # pylint: disable=C0103
        """Backup and override several objects."""
        self._call_requests_post = client._call_requests_post
        self._call_requests_put = client._call_requests_put
        self._call_requests_patch = client._call_requests_patch
        client._call_requests_post = MockPostPutPatch
        client._call_requests_put = MockPostPutPatch
        client._call_requests_patch = MockPostPutPatch

    def tearDown(self):  # pylint: disable=C0103
        """Restore backed-up objects."""
        client._call_requests_post = self._call_requests_post
        client._call_requests_put = self._call_requests_put
        client._call_requests_patch = self._call_requests_patch

    @ddt.data(
        client.patch,
        client.post,
        client.put,
    )
    def test_null(self, function):
        """Do not provide any optional args."""
        self.assertTrue(isinstance(function('example.com'), MockPostPutPatch))

    @ddt.data(
        client.patch,
        client.post,
        client.put,
    )
    def test_non_null(self, function):
        """Provide optional args. Ensure they are given to wrapped function."""
        data = 'arbitrary value'
        kwargs = {'foo': 2, 'verify': False}
        response = function('example.com', data=data, **kwargs)  # flake8:noqa pylint:disable=W0142

        self.assertTrue(isinstance(response, MockPostPutPatch))
        self.assertEqual(response.url, 'example.com')
        for key, val in kwargs.items():
            self.assertIn(key, response.kwargs.keys())
            self.assertEqual(val, response.kwargs[key])


@ddt.ddt
class ArgTestCase(TestCase):
    """Tests which inspect function arguments."""
    @ddt.data(
        (requests.delete, client._call_requests_delete),
        (requests.delete, client.delete),
        (requests.get, client._call_requests_get),
        (requests.get, client.get),
        (requests.head, client._call_requests_head),
        (requests.head, client.head),
        (requests.patch, client._call_requests_patch),
        (requests.patch, client.patch),
        (requests.post, client._call_requests_post),
        (requests.post, client.post),
        (requests.put, client._call_requests_put),
        (requests.put, client.put),
        (requests.request, client._call_requests_request),
        (requests.request, client.request),
    )
    def test_identical_args(self, functions):
        """Assert that both ``functions`` accept identical arguments."""
        self.assertEqual(
            inspect.getargspec(functions[0]),
            inspect.getargspec(functions[1]),
        )
