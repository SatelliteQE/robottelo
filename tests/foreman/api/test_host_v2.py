"""Unit tests for the "host" resource.

Each ``TestCase`` subclass tests a single URL. A full list of URLs comprising
the "host" resource can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html.

"""
from random import randint
from robottelo.api import client
from robottelo.common.decorators import skip_if_bz_bug_open
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
        """@Test: GET ``self.path``.

        @Feature: Host
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
        categories = response.json().keys()
        for category in (
                u'total', u'subtotal', u'page', u'per_page', u'search',
                u'sort', u'results'):
            self.assertIn(category, categories)

    def test_get_search(self):
        """@Test: GET ``self.path`` and specify the ``search`` parameter.

        @Feature: Host
        @Assert: Search term is returned

        """
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
        """@Test: GET ``self.path`` and specify the ``per_page`` parameter.

        @Feature: Host
        @Assert: Per page value is returned

        """
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
        """@Test: GET ``self.path`` and do not provide credentials.

        @Feature: Host
        @Assert: HTTP 401 is returned

        """
        response = client.get(self.path, verify=False)
        self.assertEqual(response.status_code, 401)

    @skip_if_bz_bug_open('1113272')
    def test_post(self):
        """@Test: POST ``self.path``.

        @Feature: Host
        @Assert: New host is created

        """
        # FIXME: use a factory to populate the POST request arguments
        response = client.post(
            self.path,
            {'host[name]': 'pie-in-the-sky'},
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200, response.json()['error'])

    def test_post_unauthorized(self):
        """@Test: POST ``self.path`` and do not provide credentials.

        @Feature: Host
        @Assert: HTTP 401 is returned

        """
        response = client.post(self.path, verify=False)
        self.assertEqual(response.status_code, 401)
