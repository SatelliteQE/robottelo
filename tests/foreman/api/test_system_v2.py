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
from robottelo import factory
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


class EntityIdTestCaseClone(TestCase):
    """Issue HTTP requests to various ``systems/:uuid`` paths."""
    def test_get_status_code(self):
        """
        @Test: Create a system and GET it.
        @Feature: Systems
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
        """
        @Test: Issue a PUT request and check the returned status code.
        @Feature: Systems
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

    def test_delete_status_code(self):
        """
        @Test: Issue an HTTP DELETE request and check the returned status
        code.
        @Feature: Systems
        @Assert: HTTP 200, 202 or 204 is returned with an ``application/json``
        content-type.

        """
        try:
            attrs = System().create()
        except factory.FactoryError as err:
            self.fail(err)
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

        # According to RFC 2616, HTTP 204 responses "MUST NOT include a
        # message-body". If a message does not have a body, there is no need to
        # set the content-type of the message.
        if response.status_code is not httplib.NO_CONTENT:
            self.assertIn('application/json', response.headers['content-type'])


class LongMessageTestCaseClone(TestCase):
    """Issue a variety of HTTP requests to a variety of URLs."""
    longMessage = True

    @skip_if_bug_open('bugzilla', 1133097)
    def test_put_and_get(self):
        """
        @Test: Issue a PUT request and GET the updated system.
        @Feature: Systems
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
        """
        @Test: Issue a POST request and GET the created system.
        @Feature: Systems
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

    @skip_if_bug_open('bugzilla', 1133071)
    def test_delete_and_get(self):
        """
        @Test: Issue an HTTP DELETE request and GET the deleted system.
        @Feature: Systems
        @Assert: An HTTP 404 is returned when fetching the missing system.
        """
        try:
            attrs = System().create()
        except factory.FactoryError as err:
            self.fail(err)
        System(uuid=attrs['uuid']).delete()

        # Get the now non-existent system
        path = System(uuid=attrs['uuid']).path()
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
