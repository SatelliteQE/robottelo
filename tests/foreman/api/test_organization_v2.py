"""Unit tests for the ``organizations`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/organizations

"""
from robottelo.api import client
from robottelo.common.decorators import skip_if_bz_bug_open
from robottelo.common.helpers import get_server_url, get_server_credentials
from robottelo import entities
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


class OrganizationsTestCase(TestCase):
    """Tests for path ``api/v2/organizations``."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/organizations')

    @skip_if_bz_bug_open(1116043)
    def test_post(self):
        """@Test: POST ``api/v2/organizations``.

        @Feature: Organization
        @Assert: HTTP 201 is returned

        """
        response = client.post(
            self.path,
            entities.Organization().attributes('api'),
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
