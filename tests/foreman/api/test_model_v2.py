"""Unit tests for the "model" resource.

Each ``TestCase`` subclass tests a single URL. A full list of URLs comprising
the "host" resource can be found here:
http://theforeman.org/api/apidoc/v2/models.html.

"""
from fauxfactory import FauxFactory
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
        categories = response.json().keys()
        for category in (
                u'total', u'subtotal', u'page', u'per_page', u'search',
                u'sort', u'results'):
            self.assertIn(category, categories)

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
            {
                'model[name]': FauxFactory.generate_string(
                    'utf8', FauxFactory.generate_integer(1, 100)
                )
            },
            auth=get_server_credentials(),
            verify=False,
        )

        status_code = 201
        self.assertEqual(
            status_code,
            response.status_code,
            'Desired HTTP {0}, got HTTP {1}. {2}'.format(
                status_code,
                response.status_code,
                response.json().get('error', 'No error received.')
            )
        )

    def test_post_unauthorized(self):
        """@Test: POST ``self.path`` and do not provide credentials.

        @Feature: Model
        @Assert: HTTP 401 is returned

        """
        response = client.post(self.path, verify=False)
        self.assertEqual(response.status_code, 401)
