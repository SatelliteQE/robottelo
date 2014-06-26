"""Unit tests for the "host" resource.

Each ``TestCase`` subclass tests a single URL. A full list of URLs comprising
the "host" resource can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html.

"""
from random import randint
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


class ApiHostsTestCase(TestCase):
    """Tests for the ``api/v2/hosts`` path."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/hosts')

    def test_get(self):
        """GET ``self.path``."""
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

    def test_get_search(self):
        """GET ``self.path`` and specify the ``search`` parameter."""
        query = 'g1JwBs3bz8s8uxaQb4Qv'  # FIXME: make this a random UTF-8 str
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            params={'search': query},
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['search'], query)

    def test_get_per_page(self):
        """GET ``self.path`` and specify the ``per_page`` parameter."""
        per_page = randint(1, 1000)
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            params={'per_page': per_page},
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['per_page'], per_page)

    def test_get_unauthorized(self):
        """GET ``self.path`` and do not provide credentials."""
        response = client.get(self.path, verify=False)
        self.assertEqual(response.status_code, 401)

    def test_post(self):
        """POST ``self.path``."""
        # FIXME: use a factory to populate the POST request arguments
        response = client.post(
            self.path,
            {'host[name]': 'pie-in-the-sky'},
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200, response.json()['error'])

    def test_post_unauthorized(self):
        """POST ``self.path`` and do not provide credentials."""
        response = client.post(self.path, verify=False)
        self.assertEqual(response.status_code, 401)
