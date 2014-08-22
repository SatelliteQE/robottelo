"""Unit tests for the ``systems`` paths.

Systems are a bit unusual. A :class:`robottelo.entities.System` has both an ID
and a UUID, but whereas most entities are uniquely identified by their ID, a
``System`` is uniquely identified by its UUID.

:class:`EntityIdTestCaseClone` and :class:`LongMessageTestCaseClone` are clones
of :class:`tests.foreman.api.test_multiple_paths.EntityIdTestCase` and
:class:`tests.foreman.api.test_multiple_paths.LongMessageTestCase`,
respsectively. This is unfortuante but necessary: those tests assume that an ID
is used to uniquely identify an entity, and cannot easily be adapted to act
otherwise.

A full list of system-related URLs can be found here:
http://theforeman.org/api/apidoc/v2/systems.html

"""
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo.entities import System
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


class EntityIdTestCaseClone(TestCase):
    """Issue HTTP requests to various ``systems/:uuid`` paths."""
    def test_get_status_code(self):
        """@Test: Create a system and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        attrs = System().create()
        path = System(uuid=attrs['uuid']).path()
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

    def test_put_status_code(self):
        """@Test Issue a PUT request and check the returned status code.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        path = System(uuid=System().create()['uuid']).path()
        response = client.put(
            path,
            System().attributes(),
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

    @skip_if_bug_open('bugzilla', 1133071)
    def test_delete(self):
        """@Test Create a system, fetch it, DELETE it, and fetch it again.

        @Assert DELETE succeeds. HTTP 200, 202 or 204 is returned before
        deleting the system, and 404 is returned after deleting the system.

        """
        attrs = System().create()
        path = System(uuid=attrs['uuid']).path()
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


class LongMessageTestCaseClone(TestCase):
    """Issue a variety of HTTP requests to a variety of URLs."""
    longMessage = True

    @skip_if_bug_open('bugzilla', 1133097)
    def test_put_and_get(self):
        """@Test: Issue a PUT request and GET the updated system.

        @Assert: The updated system has the correct attributes.

        """
        path = System(uuid=System().create()['uuid']).path()

        # Generate some attributes and use them to update a system.
        gen_attrs = System().attributes()
        response = client.put(
            path,
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK, path)

        # Get the just-updated system and examine its attributes.
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

    @skip_if_bug_open('bugzilla', 1133097)
    def test_post_and_get(self):
        """@Test Issue a POST request and GET the created system.

        @Assert: The created system has the correct attributes.

        """
        # Generate some attributes and use them to create a system.
        gen_attrs = System().build()
        response = client.post(
            System().path(),
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        path = System(uuid=response.json()['uuid']).path()
        self.assertIn(
            response.status_code, (httplib.OK, httplib.CREATED), path
        )

        # Get the just-created system and examine its attributes.
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
