"""Unit tests for the ``operatingsystems`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/operatingsystems

"""
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from robottelo import entities
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


class OperatingsystemsTestCase(TestCase):
    """Tests for path ``api/v2/operatingsystems``."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.path``."""
        self.path = urljoin(get_server_url(), 'api/v2/operatingsystems')

    def test_get(self):
        """@Test: GET ``self.path``.

        @Feature: OperatingSystem
        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

    def test_get_unauthorized(self):
        """@Test: GET ``self.path`` and do not provide credentials.

        @Feature: OperatingSystem
        @Assert: HTTP 401 is returned

        """
        response = client.get(self.path, verify=False)
        self.assertEqual(response.status_code, 401)

    def test_post(self):
        """@Test: POST ``self.path``.

        @Feature: OperatingSystem
        @Assert: HTTP 201 is returned

        """
        response = client.post(
            self.path,
            entities.OperatingSystem().attributes('api'),
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

        @Feature: OperatingSystem
        @Assert: HTTP 401 is returned

        """
        response = client.post(self.path, verify=False)
        self.assertEqual(response.status_code, 401)


class OperatingsystemsIdTestCase(TestCase):
    """Tests for path ``api/v2/operatingsystems/:id``."""
    def setUp(self):  # pylint: disable=C0103
        """Set ``self.attrs`` and ``self.path``."""
        self.attrs = entities.OperatingSystem().create()
        self.path = urljoin(
            get_server_url(),
            'api/v2/operatingsystems/{0}'.format(self.attrs['id'])
        )

    def test_get(self):
        """@Test: GET ``self.path``.

        @Feature OperatingSystem
        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

    def test_delete(self):
        """@Test: DELETE ``self.path``.

        @Feature Model
        @Assert DELETE succeeds. HTTP 200 is returned before deleting entity,
        and 404 is returned after deleting entity.

        """
        response = client.delete(
            self.path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        response = client.get(
            self.path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 404)
