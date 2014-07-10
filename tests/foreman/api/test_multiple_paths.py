"""Data-driven unit tests for multiple paths."""
from ddt import data, ddt
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from robottelo import entities
from unittest import TestCase
from urlparse import urljoin
# (too many public methods) pylint: disable=R0904


@ddt
class EntityTestCase(TestCase):
    """Issue HTTP GET and POST requests to base entity URLs."""
    @data(
        entities.Architecture,
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_get(self, entity):
        """@Test GET an entity-dependent path.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            urljoin(get_server_url(), entity.Meta.api_path[0]),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.Architecture,
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_get_unauthorized(self, entity):
        """@Test: GET an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        response = client.get(
            urljoin(get_server_url(), entity.Meta.api_path[0]),
            verify=False,
        )
        self.assertEqual(response.status_code, 401)

    @data(
        entities.Architecture,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_post(self, entity):
        """@Test: POST to an entity-dependent path.

        @Assert: HTTP 201 is returned.

        """
        path = urljoin(get_server_url(), entity.Meta.api_path[0])
        response = client.post(
            path,
            entity().build(fmt='api'),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = 201
        self.assertEqual(
            status_code,
            response.status_code,
            'Desired HTTP {0} after POSTing to {1}. Got {2}. {3}'.format(
                status_code,
                path,
                response.status_code,
                response.json().get('error', 'No error received.')
            )
        )

    @data(
        entities.Architecture,
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_post_unauthorized(self, entity):
        """@Test: POST to an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        response = client.post(
            urljoin(get_server_url(), entity.Meta.api_path[0]),
            verify=False,
        )
        self.assertEqual(response.status_code, 401)


@ddt
class EntityIdTestCase(TestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""
    @data(
        entities.Architecture,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_get(self, entity):
        """@Test: Create an entity and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        attrs = entity().create()
        path = urljoin(
            get_server_url(),
            '{0}/{1}'.format(entity.Meta.api_path[0], attrs['id'])
        )
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.Architecture,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_delete(self, entity):
        """@Test Create an entity, fetch it, DELETE it, and fetch it again.

        @Assert DELETE succeeds. HTTP 200 is returned before deleting entity,
        and 404 is returned after deleting entity.

        """
        attrs = entity().create()
        path = urljoin(
            get_server_url(),
            '{0}/{1}'.format(entity.Meta.api_path[0], attrs['id'])
        )
        response = client.delete(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 200)
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, 404)
