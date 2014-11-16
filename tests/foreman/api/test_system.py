"""Unit tests for the ``systems`` paths.

Systems are a bit unusual. A :class:`robottelo.entities.System` has both an ID
and a UUID, but whereas most entities are uniquely identified by their ID, a
``System`` is uniquely identified by its UUID.

:class:`EntityIdTestCaseClone` and :class:`DoubleCheckTestCase` are clones
of :class:`tests.foreman.api.test_multiple_paths.EntityIdTestCase` and
:class:`tests.foreman.api.test_multiple_paths.DoubleCheckTestCase`,
respsectively. This is unfortuante but necessary: those tests assume that an ID
is used to uniquely identify an entity, and cannot easily be adapted to act
otherwise.

A full list of system-related URLs can be found here:
http://theforeman.org/api/apidoc/v2/systems.html

"""
import httplib
import logging
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo.entities import System
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


logger = logging.getLogger(__name__)  # pylint:disable=C0103


class EntityIdTestCaseClone(APITestCase):
    """Issue HTTP requests to various ``systems/:uuid`` paths."""

    def test_get_status_code(self):
        """@Test: Create a system and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        system = System(uuid=System().create_json()['uuid'])
        logger.debug('system uuid: {0}'.format(system.uuid))
        response = client.get(
            system.path(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(httplib.OK, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    def test_put_status_code(self):
        """@Test Issue a PUT request and check the returned status code.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        system = System(uuid=System().create_json()['uuid'])
        logger.debug('system uuid: {0}'.format(system.uuid))
        system.create_missing()
        response = client.put(
            system.path(),
            system.create_payload(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(httplib.OK, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    def test_delete_status_code(self):
        """@Test Issue an HTTP DELETE request and check the returned status
        code.

        @Assert: HTTP 200, 202 or 204 is returned with an ``application/json``
        content-type.

        """
        try:
            system = System(uuid=System().create_json()['uuid'])
        except HTTPError as err:
            self.fail(err)
        logger.debug('system uuid: {0}'.format(system.uuid))
        response = client.delete(
            system.path(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertIn(
            response.status_code,
            (httplib.NO_CONTENT, httplib.OK, httplib.ACCEPTED)
        )

        # According to RFC 2616, HTTP 204 responses "MUST NOT include a
        # message-body". If a message does not have a body, there is no need to
        # set the content-type of the message.
        if response.status_code is not httplib.NO_CONTENT:
            self.assertIn('application/json', response.headers['content-type'])


class DoubleCheckTestCase(APITestCase):
    """Perform in-depth tests on URLs.

    Do not just assume that an HTTP response with a good status code indicates
    that an action succeeded. Instead, issue a follow-up request after each
    action to ensure that the intended action was accomplished.

    """

    @skip_if_bug_open('bugzilla', 1133097)
    def test_put_and_get(self):
        """@Test: Issue a PUT request and GET the updated system.

        @Assert: The updated system has the correct attributes.

        """
        system = System(uuid=System().create_json()['uuid'])
        logger.debug('system uuid: {0}'.format(system.uuid))

        # Generate some attributes and use them to update `system`.
        system.create_missing()
        response = client.put(
            system.path(),
            system.create_payload(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)

        # Get the just-updated system and examine its attributes.
        attrs = system.read_json()
        for key, value in system.create_payload().items():
            self.assertIn(key, attrs.keys())
            self.assertEqual(value, attrs[key])

    @skip_if_bug_open('bugzilla', 1133097)
    def test_post_and_get(self):
        """@Test Issue a POST request and GET the created system.

        @Assert: The created system has the correct attributes.

        """
        system = System()
        system.uuid = system.create_json()['uuid']
        logger.debug('system uuid: {0}'.format(system.uuid))

        # Get the just-created system and examine its attributes.
        attrs = system.read_json()
        for key, value in system.create_payload().items():
            self.assertIn(key, attrs.keys())
            self.assertEqual(value, attrs[key])

    @skip_if_bug_open('bugzilla', 1133071)
    def test_delete_and_get(self):
        """@Test: Issue an HTTP DELETE request and GET the deleted system.

        @Assert: An HTTP 404 is returned when fetching the missing system.

        """
        try:
            system = System(uuid=System().create_json()['uuid'])
        except HTTPError as err:
            self.fail(err)
        logger.debug('system uuid: {0}'.format(system.uuid))
        system.delete()

        # Get the now non-existent system
        response = system.read_raw()
        self.assertEqual(httplib.NOT_FOUND, response.status_code)
