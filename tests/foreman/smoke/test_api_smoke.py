"""Smoke tests for the ``API`` end-to-end scenario."""
from nose.plugins.attrib import attr
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities, orm
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


class TestSmoke(TestCase):
    """End-to-end tests using the ``API`` path."""

    @attr('smoke')
    def test_find_default_org(self):
        """
        @Test: Check if 'Default Organization' is present
        @Feature: Smoke Test
        @Assert: 'Default Organization' is found
        """
        query = u'Default Organization'
        self._search(entities.Organization, query)

    @attr('smoke')
    def test_find_default_location(self):
        """
        @Test: Check if 'Default Location' is present
        @Feature: Smoke Test
        @Assert: 'Default Location' is found
        """
        query = u'Default Location'
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
        ok_status = all(
            [service['status'] == u'ok' for service in services.values()]
        )
        self.assertTrue(
            ok_status,
            u"Not all services seem to be up and running!"
        )

    # FIXME: This test is still being developed and is not complete yet.
    @attr('smoke')
    def test_smoke(self):
        """
        @Test: Check that basic content can be created

        1. Create a new user with admin permissions
        2. Using the new user from above:
            1. Create a new organization
            2. Create two new lifecycle environments
            3. Create a custom product
            4. Create a custom YUM repository
            5. Create a custom PUPPET repository
            6. Synchronize both custom repositories
            7. Create a new content view
            8. Associate both repositories to new content view
            9. Publish content view
            10. Promote content view to both lifecycles
            11. Create a new libvirt compute resource
            12. Create a new subnet
            13. Create a new domain
            14. Create a new capsule
            15. Create a new hostgroup and associate previous entities to it

        @Feature: Smoke Test

        @Assert: All entities are created and associated.
        """
        # prep work
        #
        # FIXME: Use a larger charset when authenticating users.
        #
        # It is possible to create a user with a wide range of characters. (see
        # the "User" entity). However, Foreman supports only HTTP Basic
        # authentication, and the requests lib enforces the latin1 charset in
        # this auth mode. We then further restrict ourselves to the
        # alphanumeric charset, because Foreman complains about incomplete
        # multi-byte chars when latin1 chars are used.
        #
        login = orm.StringField(str_type=('alphanumeric',)).get_value()
        password = orm.StringField(str_type=('alphanumeric',)).get_value()

        # step 1
        entities.User(admin=True, login=login, password=password).create()

        # step 2.1
        entities.Organization().create(auth=(login, password))

        # step 2.2
        #
        # FIXME: Creation of LifecycleEnvironment entities is broken.
        # Error message: "Couldn't find Katello::KTEnvironment with id=Library"
        #
        # le_1_attrs = entities.LifecycleEnvironment(
        #     organization=org_attrs['id']
        # ).create(auth=(login, password))
        # le_2_attrs = entities.LifecycleEnvironment(
        #     organization=org_attrs['id'],
        #     prior=le_1_attrs['name']
        # ).create(auth=(login, password))
        # entities.LifecycleEnvironment(
        #     organization=org_attrs['id'],
        #     prior=le_2_attrs['name']
        # ).create(auth=(login, password))

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
