"""Smoke tests for the ``API`` end-to-end scenario."""
from nose.plugins.attrib import attr
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


class TestSmoke(TestCase):
    """End-to-end tests using the ``API`` path."""

    @attr('smoke')
    def test_find_default_org(self):
        """
        @Test: Check if Default_Organization is present
        @Feature: Smoke Test
        @Assert: Default_Organization is found
        """
        query = u'Default_Organization'
        self._search(entities.Organization, query)

    @attr('smoke')
    def test_find_default_location(self):
        """
        @Test: Check if Default_Location is present
        @Feature: Smoke Test
        @Assert: Default_Location is found
        """
        query = u'Default_Location'
        self._search(entities.Location, query)

    @attr('smoke')
    def test_find_admin_user(self):
        """
        @Test: Check if Admin User is present
        @Feature: Smoke Test
        @Assert: Admin User is found and has Admin role
        """
        query = u'admin'
        self._search(entities.User, query)

    @attr('smoke')
    def test_ping(self):
        """
        @Test: Check if all services are running
        @Feature: Smoke Test
        @Assert: Overall and individual services status should be 'ok'.
        """
        path = entities.Ping().path()
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False)
        self.assertEqual(
            response.status_code,
            httplib.OK,
            status_code_error(path, httplib.OK, response)
        )
        # Check overal status
        self.assertEqual(
            response.json()['status'],
            u'ok',
            U"The server does not seem to be configured properly!"
        )

        # Extract all services status information returned with the format:
        # {u'services': {
        #    u'candlepin': {u'duration_ms': u'40', u'status': u'ok'},
        #    u'candlepin_auth': {u'duration_ms': u'41', u'status': u'ok'},
        #    u'elasticsearch': {u'duration_ms': u'22', u'status': u'ok'},
        #    u'katello_jobs': {u'duration_ms': u'43', u'status': u'ok'},
        #    u'pulp': {u'duration_ms': u'18', u'status': u'ok'},
        #    u'pulp_auth': {u'duration_ms': u'30', u'status': u'ok'}},
        #    u'status': u'ok'}
        services = response.json()['services']
        # Check if all services are 'OK'
        ok_status = all([
            services[key]['status'] == u'ok' for key in services.keys()
        ])
        self.assertTrue(
            ok_status,
            u"Not all services seem to be up and running!"
        )

    # FIXME: This test is still being developed and is not complete yet.
    @attr('smoke')
    def test_smoke(self):
        """
        @Test: Check that basic content can be created
            * Create a new user with admin permissions
            * Using the new user from above:
              * Create a new organization
              * Create two new lifecycle environments
              * Create a custom product
              * Create a custom YUM repository
              * Create a custom PUPPET repository
              * Synchronize both custom repositories
              * Create a new content view
              * Associate both repositories to new content view
              * Publish content view
              * Promote content view to both lifecycles
              * Create a new libvirt compute resource
              * Create a new subnet
              * Create a new domain
              * Create a new capsule
              * Create a new hostgroup and associate previous entities to it
        @Feature: Smoke Test
        @Assert: All entities are created and associated.
        """
        # Create a new user with admin permissions
        self._create(
            entities.User,
            entities.User(admin=True).build()
        )

    # FIXME: Until we can pass ``auth`` to ``Entity().crate()`` and
    # ``Entity().build()``, I need to rely on ``client.post`` to make
    # sure that certain actions can be performed by a non-default
    # admin user.
    def _create(self, entity, attrs, auth=None):
        """
        Performs a POST ``api/v2/<entity>`` and creates a new Foreman entity
        using ``attrs`` as its attributes.

        :param robottelo.orm.Entity entity: A logical representation of a
            Foreman entity.
        :param dict attrs: A ``dict`` representing a Foreman entity.
        :param tuple auth: A ``tuple`` containing the credentials to be used
            for authentication when accessing the API. If ``None``,
            credentials are automatically read from
            :func:`robottelo.common.helpers.get_server_credentials`.
        :return: A ``dict`` representing a Foreman entity.
        :rtype: dict
        """
        # Use the server credentials if None are provided
        if auth is None:
            auth = get_server_credentials()

        path = entity().path()
        response = client.post(
            path,
            attrs,
            auth=auth,
            verify=False,
        )
        status_code = (httplib.OK, httplib.CREATED)
        self.assertIn(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response))

        return response.json()

    def _search(self, entity, query, auth=None):
        """
        Performs a GET ``api/v2/<entity>`` and specify the ``search``
        parameter.

        :param robottelo.orm.Entity entity: A logical representation of a
            Foreman entity.
        :param string query: A ``search`` parameter.
        :param tuple auth: A ``tuple`` containing the credentials to be used
            for authentication when accessing the API. If ``None``,
            credentials are automatically read from
            :func:`robottelo.common.helpers.get_server_credentials`.
        :return: A ``dict`` representing a Foreman entity.
        :rtype: dict
        """
        # Use the server credentials if None are provided
        if auth is None:
            auth = get_server_credentials()

        path = entity().path()
        response = client.get(
            path,
            auth=auth,
            params={'search': query},
            verify=False,
        )
        self.assertEqual(
            response.status_code,
            httplib.OK,
            status_code_error(path, httplib.OK, response)
        )
        self.assertEqual(
            response.json()['search'],
            query,
            u"Could not find {0}.".format(query)
        )

        return response.json()
