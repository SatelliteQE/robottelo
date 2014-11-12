"""Smoke tests for the ``API`` end-to-end scenario."""
from nose.plugins.attrib import attr
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.constants import FAKE_PUPPET_REPO, GOOGLE_CHROME_REPO
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo.common import helpers
from robottelo import entities, orm
from unittest import TestCase
import httplib
import random
# (too many public methods) pylint: disable=R0904

# Note: Commenting three urls below since BZ 1105773 is fixed in upstream only
API_PATHS = frozenset((
    # pylint:disable=C0301
    u'/api',
    u'/api/architectures',
    u'/api/audits',
    u'/api/auth_source_ldaps',
    u'/api/bookmarks',
    u'/api/common_parameters',
    u'/api/compute_profiles',
    u'/api/compute_resources',
    u'/api/compute_resources/:compute_resource_id/images',
    u'/api/config_groups',
    u'/api/config_templates',
    u'/api/config_templates/:config_template_id/template_combinations',
    u'/api/dashboard',
    u'/api/discovered_hosts',
    u'/api/domains',
    u'/api/environments',
    u'/api/fact_values',
    u'/api/filters',
    u'/api/hostgroups',
    u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
    u'/api/hosts',
    u'/api/hosts/:host_id/interfaces',
    u'/api/hosts/:host_id/parameters',
    u'/api/hosts/:host_id/puppetclass_ids',
    u'/api/locations',
    u'/api/media',
    u'/api/models',
    u'/api/operatingsystems',
    u'/api/operatingsystems/:operatingsystem_id/os_default_templates',
    u'/api/orchestration/:id/tasks',
    u'/api/permissions',
    u'/api/plugins',
    u'/api/ptables',
    u'/api/puppetclasses',
    u'/api/realms',
    u'/api/reports',
    u'/api/roles',
    u'/api/settings',
    u'/api/smart_class_parameters',
    u'/api/smart_proxies',
    u'/api/smart_proxies/smart_proxy_id/autosign',
    u'/api/smart_variables',
    u'/api/smart_variables/:smart_variable_id/override_values',
    u'/api/statistics',
    u'/api/status',
    u'/api/subnets',
    u'/api/template_kinds',
    u'/api/usergroups',
    u'/api/users',
    # u'/foreman_tasks/api/tasks/:id',  # WTF
    u'/katello/api/activation_keys',
    u'/katello/api/capsules',
    u'/katello/api/content_view_filters/:content_view_filter_id/rules',
    u'/katello/api/content_views/:content_view_id/content_view_puppet_modules',
    u'/katello/api/content_views/:content_view_id/filters',
    u'/katello/api/content_view_versions',
    u'/katello/api/environments',
    u'/katello/api/errata',
    u'/katello/api/gpg_keys',
    u'/katello/api/host_collections',
    u'/katello/api/organizations',
    u'/katello/api/organizations/:organization_id/content_views',
    u'/katello/api/organizations/:organization_id/host_collections/:host_collection_id/errata',  # flake8:noqa
    # u'/katello/api/organizations/:organization_id/host_collections/:host_collection_id/packages',  # flake8:noqa
    u'/katello/api/organizations/:organization_id/products/:product_id/sync',
    u'/katello/api/organizations/:organization_id/subscriptions',
    u'/katello/api/organizations/:organization_id/sync_plans',
    u'/katello/api/package_groups',
    u'/katello/api/ping',
    u'/katello/api/products',
    u'/katello/api/products/:product_id/repository_sets',
    u'/katello/api/puppet_modules',
    u'/katello/api/repositories',
    u'/katello/api/repositories/:repository_id/distributions',
    u'/katello/api/repositories/:repository_id/packages',
    u'/katello/api/systems',
    # u'/katello/api/systems/:system_id/errata',
))


class TestAvailableURLs(TestCase):
    """Tests for ``api/v2``."""
    def setUp(self):
        """Define commonly-used variables."""
        self.path = '{0}/api/v2'.format(helpers.get_server_url())

    def test_get_status_code(self):
        """@Test: GET ``api/v2`` and examine the response.

        @Feature: API

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            self.path,
            auth=helpers.get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('application/json', response.headers['content-type'])

    @skip_if_bug_open('bugzilla', 1105773)
    def test_get_links(self):
        """@Test: GET ``api/v2`` and check the links returned.

        @Feature: API

        @Assert: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(
            self.path,
            auth=helpers.get_server_credentials(),
            verify=False,
        ).json()
        self.assertIn('links', response.keys())
        links = response['links']

        # Did the server give us correct paths?
        self.assertEqual(API_PATHS, frozenset(links.values()))

        # Even if the server gave us exactly the right paths, its response
        # might still be wrong. What if it the response contained duplicate
        # paths?
        self.assertEqual(len(API_PATHS), len(links))


class TestSmoke(TestCase):
    """End-to-end tests using the ``API`` path."""

    @attr('smoke')
    def test_find_default_org(self):
        """
        @Test: Check if 'Default Organization' is present
        @Feature: Smoke Test
        @Assert: 'Default Organization' is found
        """
        query = u'Default_Organization'
        self._search(entities.Organization, query)

    @attr('smoke')
    def test_find_default_location(self):
        """
        @Test: Check if 'Default Location' is present
        @Feature: Smoke Test
        @Assert: 'Default Location' is found
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
            14. Create a new hostgroup and associate previous entities to it

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

        # step 1: Create a new user with admin permissions
        entities.User(admin=True, login=login, password=password).create()

        # step 2.1: Create a new organization
        org = entities.Organization().create(auth=(login, password))

        # step 2.2: Create 2 new lifecycle environments
        le1 = entities.LifecycleEnvironment(organization=org['id']).create()
        le2 = entities.LifecycleEnvironment(
            organization=org['id'], prior=le1['id']).create()

        # step 2.3: Create a custom product
        prod = entities.Product(organization=org['id']).create()

        # step 2.4: Create custom YUM repository
        repo1 = entities.Repository(
            product=prod['id'],
            content_type=u'yum',
            url=GOOGLE_CHROME_REPO
        ).create()

        # step 2.5: Create custom PUPPET repository
        repo2 = entities.Repository(
            product=prod['id'],
            content_type=u'puppet',
            url=FAKE_PUPPET_REPO
        ).create()

        # step 2.6: Synchronize both repositories
        for repo in [repo1, repo2]:
            response = client.post(
                entities.Repository(id=repo['id']).path('sync'),
                {
                    u'ids': [repo['id']],
                    u'organization_id': org['id']
                },
                auth=get_server_credentials(),
                verify=False,
            ).json()
            self.assertGreater(
                len(response['id']),
                1,
                u"Was not able to fetch a task ID.")
            task_status = entities.ForemanTask(id=response['id']).poll()
            self.assertEqual(
                task_status['result'],
                u'success',
                u"Sync for repository {0} failed.".format(repo['name']))

        # step 2.7: Create content view
        content_view = entities.ContentView(organization=org['id']).create()

        # step 2.8: Associate YUM repository to new content view
        response = client.put(
            entities.ContentView(id=content_view['id']).path(),
            auth=get_server_credentials(),
            verify=False,
            data={u'repository_ids': [repo1['id']]})

        # Fetch all available puppet modules
        puppet_mods = client.get(
            entities.ContentView(id=content_view['id']).path(
                'available_puppet_module_names'),
            auth=get_server_credentials(),
            verify=False).json()
        self.assertGreater(
            puppet_mods['results'],
            0,
            u"No puppet modules were found")

        # Select a random puppet module from the results
        puppet_mod = random.choice(puppet_mods['results'])
        # ... and associate it to the content view
        path = entities.ContentView(id=content_view['id']).path(
            'content_view_puppet_modules')
        response = client.post(
            path,
            auth=get_server_credentials(),
            verify=False,
            data={u'name': puppet_mod['module_name']})
        self.assertEqual(
            response.status_code,
            httplib.OK,
            status_code_error(path, httplib.OK, response)
        )
        self.assertEqual(
            response.json()['name'],
            puppet_mod['module_name'],
        )

        # step 2.9: Publish content view
        task = entities.ContentView(id=content_view['id']).publish()
        task_status = entities.ForemanTask(id=task['id']).poll()
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Publishing {0} failed.".format(content_view['name']))

        # step 2.10: Promote content view to both lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            1,
            u"Content view should be present on 1 lifecycle only")
        task = entities.ContentViewVersion(
            id=content_view['versions'][0]['id']).promote(le1['id'])
        task_status = entities.ForemanTask(id=task['id']).poll()
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Promoting {0} to {1} failed.".format(
                content_view['name'], le1['name']))
        # Check that content view exists in 2 lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            2,
            u"Content view should be present on 2 lifecycles only")
        task = entities.ContentViewVersion(
            id=content_view['versions'][0]['id']).promote(le2['id'])
        task_status = entities.ForemanTask(id=task['id']).poll()
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Promoting {0} to {1} failed.".format(
                content_view['name'], le2['name']))
        # Check that content view exists in 2 lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            3,
            u"Content view should be present on 3 lifecycle only")

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host = entities.System(
            content_view=content_view['id'],
            environment=le2['id']
        ).create()
        # Check that content view matches what we passed
        self.assertEqual(
            content_host['content_view_id'],
            content_view['id'],
            u"Content views do not match."
        )
        # Check that lifecycle environment matches
        self.assertEqual(
            content_host['environment']['id'],
            le2['id'],
            u"Environments do not match."
        )


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
            data={u'search': query},
            verify=False,
        )
        response.raise_for_status()
        self.assertEqual(
            response.json()['search'],
            query,
            u"Could not find {0}.".format(query)
        )

        return response.json()
