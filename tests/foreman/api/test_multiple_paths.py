"""Data-driven unit tests for multiple paths."""
from ddt import data, ddt
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@ddt
class EntityTestCase(TestCase):
    """Issue HTTP requests to various ``entity/`` paths."""
    @data(
        entities.Architecture,
        entities.Domain,
        # entities.GPGKey,  # must specify an organization id
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_get_status_code(self, entity):
        """@Test GET an entity-dependent path.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        path = entity().path()
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.Architecture,
        entities.Domain,
        entities.GPGKey,
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
    )
    def test_get_unauthorized(self, entity):
        """@Test: GET an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        path = entity().path()
        response = client.get(path, verify=False)
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )

    @data(
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_post_status_code(self, entity):
        """@Test: Issue a POST request and check the returned status code.

        @Assert: HTTP 201 is returned with an ``application/json`` content-type

        """
        path = entity().path()
        response = client.post(
            path,
            entity().build(),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.CREATED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Host,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_post_unauthorized(self, entity):
        """@Test: POST to an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        path = entity().path()
        response = client.post(path, verify=False)
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )


@ddt
class EntityIdTestCase(TestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""
    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_get_status_code(self, entity):
        """@Test: Create an entity and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        attrs = entity().create()
        path = entity(id=attrs['id']).path()
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_put_status_code(self, entity):
        """@Test Issue a PUT request and check the returned status code.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        path = entity(id=entity().create()['id']).path()
        response = client.put(
            path,
            entity().attributes(),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
        entities.User,
    )
    def test_delete(self, entity):
        """@Test Create an entity, fetch it, DELETE it, and fetch it again.

        @Assert DELETE succeeds. HTTP 200, 202 or 204 is returned before
        deleting entity, and 404 is returned after deleting entity.

        """
        attrs = entity().create()
        path = entity(id=attrs['id']).path()
        response = client.delete(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = (httplib.NO_CONTENT, httplib.OK, httplib.ACCEPTED)
        self.assertIn(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
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
            status_code_error(path, status_code, response),
        )


@ddt
class LongMessageTestCase(TestCase):
    """Issue a variety of HTTP requests to a variety of URLs."""
    longMessage = True

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_put_and_get(self, entity):
        """@Test: Issue a PUT request and GET the updated entity.

        @Assert: The updated entity has the correct attributes.

        """
        path = entity(id=entity().create()['id']).path()

        # Generate some attributes and use them to update an entity.
        gen_attrs = entity().attributes()
        response = client.put(
            path,
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK, path)

        # Get the just-updated entity and examine its attributes.
        real_attrs = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        for key, value in gen_attrs.items():
            self.assertIn(key, real_attrs.keys(), path)
            self.assertEqual(
                value, real_attrs[key], '{0} {1}'.format(key, path)
            )

    @data(
        entities.Architecture,
        entities.ContentView,
        entities.Domain,
        entities.GPGKey,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Repository,
    )
    def test_post_and_get(self, entity):
        """@Test Issue a POST request and GET the created entity.

        @Assert: The created entity has the correct attributes.

        """
        # Generate some attributes and use them to create an entity.
        gen_attrs = entity().build()
        response = client.post(
            entity().path(),
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        path = entity(id=response.json()['id']).path()
        self.assertIn(
            response.status_code, (httplib.OK, httplib.CREATED), path
        )

        # Get the just-created entity and examine its attributes.
        real_attrs = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        for key, value in gen_attrs.items():
            self.assertIn(key, real_attrs.keys(), path)
            self.assertEqual(
                value, real_attrs[key], '{0} {1}'.format(key, path)
            )
