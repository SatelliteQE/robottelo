"""Unit tests for the ``architectures`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/architectures

"""
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from robottelo import entities
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


class ArchitecturesTestCase(TestCase):
    """Tests for path ``api/v2/architectures``."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/architectures')

    def test_post(self):
        """@Test: POST ``api/v2/architectures``.

        @Feature: Architecture
        @Assert: HTTP 201 is returned

        """
        response = client.post(
            self.path,
            entities.Architecture().attributes('api'),
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
