"""Data-driven unit tests for multiple paths."""
from ddt import data, ddt
from robottelo.api import client
from robottelo.common.helpers import get_server_url, get_server_credentials
from robottelo import entities
from unittest import TestCase
from urlparse import urljoin
import httplib
# (too many public methods) pylint: disable=R0904


def _status_code_error(path, desired, response):
    """Return an error message.

    ``desired`` and ``path`` are used as-is. The following must be present on
    ``response``:

    * ``response.status_code``
    * ``response.json()``

    :param int desired: The desired return status code.
    :param str path: The path to which a request was sent.
    :param response: The ``Response`` object returned.
    :return: An error message.
    :rtype: str

    """
    try:
        err_msg = response.json().get('error', 'No error message provided.')
    except ValueError:
        err_msg = 'Could not decode response; not in JSON format.'
    return 'Desired HTTP {0} but received HTTP {1} after sending request to ' \
        '{2}. {3}'.format(desired, response.status_code, path, err_msg)


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
        path = urljoin(get_server_url(), entity.Meta.api_path[0])
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )
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
        path = urljoin(get_server_url(), entity.Meta.api_path[0])
        response = client.get(path, verify=False)
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )

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
        status_code = httplib.CREATED
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
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
        path = urljoin(get_server_url(), entity.Meta.api_path[0])
        response = client.post(path, verify=False)
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )


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
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.Architecture,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_put(self, entity):
        """@Test Create an entity and update (PUT) it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        attrs = entity().create()
        path = urljoin(
            get_server_url(),
            '{0}/{1}'.format(entity.Meta.api_path[0], attrs['id'])
        )
        response = client.put(
            path,
            entity().attributes(fmt='api'),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )
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
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.NOT_FOUND
        self.assertEqual(
            status_code,
            response.status_code,
            _status_code_error(path, status_code, response),
        )
