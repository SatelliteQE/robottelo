"""Unit tests for the "model" resource.

Each ``TestCase`` subclass tests a single URL. A full list of URLs comprising
the "host" resource can be found here:
http://theforeman.org/api/apidoc/v2/models.html.

"""
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


class ApiModelsTestCase(TestCase):
    """Tests for the ``api/v2/models/`` path."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/models')

    def test_get(self):
        """@Test: GET ``self.path``.

        @Feature: Model
        @Assert: GET succeeds

        """
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            verify=False
        )

        # Run sanity checks.
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

        # Are the correct categories of data returned?
        data = response.json()
        data_keys = data.keys()
        self.assertIn(u'total', data_keys)
        self.assertIn(u'subtotal', data_keys)
        self.assertIn(u'page', data_keys)
        self.assertIn(u'per_page', data_keys)
        self.assertIn(u'search', data_keys)
        self.assertIn(u'sort', data_keys)
        self.assertIn(u'results', data_keys)

    def test_get_unauthorized(self):
        """@Test: GET ``self.path`` and do not provide credentials.

        @Feature: Model
        @Assert: HTTP 401 is returned

        """
        response = client.get(self.path, verify=False)
        self.assertEqual(response.status_code, 401)

    def test_post(self):
        """@Test: POST ``self.path``.

        @Feature: Model
        @Assert: New host is created

        """
        # FIXME: use a factory to populate the POST request arguments
        response = client.post(
            self.path,
            {'model[name]': 'Z62RNEc9J4kbUXOHJiYE'},
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200, response.json()['error'])

    def test_post_unauthorized(self):
        """@Test: POST ``self.path`` and do not provide credentials.

        @Feature: Model
        @Assert: HTTP 401 is returned

        """
        response = client.post(self.path, verify=False)
        self.assertEqual(response.status_code, 401)
