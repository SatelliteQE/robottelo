"""Unit tests for the ``hosts`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/hosts

"""
from fauxfactory import FauxFactory
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from unittest import TestCase
from urlparse import urljoin
import httplib
# (too many public methods) pylint: disable=R0904


class HostsTestCase(TestCase):
    """Tests for path ``api/v2/hosts``."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/hosts')

    def test_get_search(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``search`` parameter.

        @Feature: Host
        @Assert: HTTP 200 is returned, along with ``search`` term.

        """
        query = FauxFactory.generate_string(
            'utf8',
            FauxFactory.generate_integer(1, 100)
        )
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            params={'search': query},
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['search'], query)

    def test_get_per_page(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

        @Feature: Host
        @Assert: HTTP 200 is returned, along with per ``per_page`` value.

        """
        per_page = FauxFactory.generate_integer(1, 1000)
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            params={'per_page': per_page},
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['per_page'], per_page)
