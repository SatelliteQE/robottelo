"""Unit tests for module ``robottelo.api.client``."""
from fauxfactory import gen_alpha
from robottelo.api import client
from unittest import TestCase
from urllib import urlencode
import ddt
import inspect
import mock
import requests
# (accessing private members) pylint: disable=W0212
# (too many public methods) pylint: disable=R0904


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
    def setUp(self):
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


class ClientTestCase(TestCase):
    """Tests for functions in :mod:`robottelo.api.client`."""

    def setUp(self):
        self.bogus_url = gen_alpha()
        self.mock_response = mock.Mock()

    def test_clients(self):
        """Test ``delete``, ``get``, ``head``, ``patch``, ``post`` and ``put``.

        Assert that:

        * The outer function (e.g. ``delete``) returns whatever the inner
          function (e.g. ``_call_requests_delete``) returns.
        * The outer function passes the correct parameters to the inner
          function.

        """
        for outer, inner in (
                (client.delete, 'robottelo.api.client._call_requests_delete'),
                (client.get, 'robottelo.api.client._call_requests_get'),
                (client.head, 'robottelo.api.client._call_requests_head'),
                (client.patch, 'robottelo.api.client._call_requests_patch'),
                (client.post, 'robottelo.api.client._call_requests_post'),
                (client.put, 'robottelo.api.client._call_requests_put')):
            with mock.patch(
                inner,
                return_value=self.mock_response
            ) as mock_inner:
                self.assertIs(outer(self.bogus_url), self.mock_response)
                if outer in (client.delete, client.get, client.head):
                    mock_inner.assert_called_once_with(
                        self.bogus_url,
                        headers={'content-type': 'application/json'}
                    )
                elif outer in (client.patch, client.put):
                    mock_inner.assert_called_once_with(
                        self.bogus_url,
                        None,
                        headers={'content-type': 'application/json'}
                    )
                else:  # outer is client.post
                    mock_inner.assert_called_once_with(
                        self.bogus_url,
                        None,
                        None,
                        headers={'content-type': 'application/json'}
                    )

    def test_client_request(self):
        """Test :func:`robottelo.api.client.request`.

        Assert that:

        * ``request`` returns whatever ``_call_requests_request`` returns.
        * ``request`` passes the correct parameters to
          ``_call_requests_request``.

        """
        with mock.patch(
            'robottelo.api.client._call_requests_request',
            return_value=self.mock_response
        ) as mock_inner:
            self.assertIs(
                client.request('foo', self.bogus_url),
                self.mock_response,
            )
            mock_inner.assert_called_once_with(
                'foo',
                self.bogus_url,
                headers={'content-type': 'application/json'}
            )


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
