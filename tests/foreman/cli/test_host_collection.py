# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.factory import (
    CLIFactoryError, make_org, make_host_collection, make_content_view,
    make_lifecycle_environment, make_content_host)
from robottelo.cli.hostcollection import HostCollection
from robottelo.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestHostCollection(CLITestCase):
    """Host Collection CLI tests."""

    org = None
    new_cv = None
    promoted_cv = None
    new_lifecycle = None
    library = None
    default_cv = None

    def setUp(self):  # noqa
        """Tests for Host Collections via Hammer CLI"""
        super(TestHostCollection, self).setUp()

        if TestHostCollection.org is None:
            TestHostCollection.org = make_org(cached=True)
        if TestHostCollection.new_lifecycle is None:
            TestHostCollection.new_lifecycle = make_lifecycle_environment(
                {u'organization-id': TestHostCollection.org['id']},
                cached=True
            )
        if TestHostCollection.library is None:
            result = LifecycleEnvironment.info({
                u'organization-id': TestHostCollection.org['id'],
                u'name': u'Library',
            })
            self.assertEqual(result.return_code, 0)
            TestHostCollection.library = result.stdout
        if TestHostCollection.default_cv is None:
            result = ContentView.info(
                {u'organization-id': TestHostCollection.org['id'],
                 u'name': u'Default Organization View'}
            )
            self.assertEqual(result.return_code, 0)
            TestHostCollection.default_cv = result.stdout
        if TestHostCollection.new_cv is None:
            TestHostCollection.new_cv = make_content_view(
                {u'organization-id': TestHostCollection.org['id']}
            )
            TestHostCollection.promoted_cv = None
            cv_id = TestHostCollection.new_cv['id']
            result = ContentView.publish({u'id': cv_id})
            self.assertEqual(result.return_code, 0)
            result = ContentView.version_list({u'content-view-id': cv_id})
            self.assertEqual(result.return_code, 0)
            version_id = result.stdout[0]['id']
            result = ContentView.version_promote({
                u'id': version_id,
                u'to-lifecycle-environment-id': (
                    TestHostCollection.new_lifecycle['id']),
                u'organization-id': TestHostCollection.org['id']
            })
            self.assertEqual(result.return_code, 0)
            TestHostCollection.promoted_cv = TestHostCollection.new_cv

    def _new_host_collection(self, options=None):
        """Make a host collection and asserts its success"""
        if options is None:
            options = {}
        if not options.get('organization-id', None):
            options['organization-id'] = self.org['id']

        return make_host_collection(options)

    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_create_1(self, test_data):
        """@Test: Check if host collection can be created with random names

        @Feature: Host Collection

        @Assert: Host collection is created and has random name

        """

        new_host_col = self._new_host_collection({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(new_host_col['name'], test_data['name'])

    @data(
        {'description': gen_string('alpha', 15)},
        {'description': gen_string('alphanumeric', 15)},
        {'description': gen_string('numeric', 15)},
        {'description': gen_string('latin1', 15)},
        {'description': gen_string('utf8', 15)},
        {'description': gen_string('html', 15)},
    )
    def test_positive_create_2(self, test_data):
        """@Test: Check if host collection can be created with random description

        @Feature: Host Collection

        @Assert: Host collection is created and has random description

        """

        new_host_col = self._new_host_collection({
            'description': test_data['description'],
        })
        # Assert that description matches data passed
        self.assertEqual(new_host_col['description'], test_data['description'])

    @data('1', '3', '5', '10', '20')
    def test_positive_create_3(self, test_data):
        """@Test: Check if host collection can be created with random limits

        @Feature: Host Collection

        @Assert: Host collection is created and has random limits

        """

        new_host_col = self._new_host_collection({
            'max-content-hosts': test_data,
        })
        # Assert that limit matches data passed
        self.assertEqual(new_host_col['limit'], str(test_data))

    @skip_if_bug_open('bugzilla', 1214675)
    @data(u'True', u'Yes', 1, u'False', u'No', 0)
    def test_create_hc_with_unlimited_content_hosts(self, unlimited):
        """@Test: Create Host Collection with different values of
        unlimited-content-hosts parameter

        @Feature: Host Collection - Unlimited Content Hosts

        @Assert: Host Collection is created and unlimited-content-hosts
        parameter is set

        @BZ: 1214675

        """
        try:
            host_collection = make_host_collection({
                u'organization-id': self.org['id'],
                u'unlimited-content-hosts': unlimited,
            })
        except CLIFactoryError as err:
            self.fail(err)
        result = HostCollection.info({
            u'id': host_collection['id'],
            u'organization-id': self.org['id'],
        })
        if unlimited in (u'True', u'Yes', 1):
            self.assertEqual(
                result.stdout['unlimited-content-hosts'], u'true')
        else:
            self.assertEqual(
                result.stdout['unlimited-content-hosts'], u'false')

    @data(
        {'name': gen_string('alpha', 300)},
        {'name': gen_string('alphanumeric', 300)},
        {'name': gen_string('numeric', 300)},
        {'name': gen_string('latin1', 300)},
        {'name': gen_string('utf8', 300)},
        {'name': gen_string('html', 300)},
    )
    def test_negative_create_1(self, test_data):
        """@Test: Check if host collection can be created with random names

        @Feature: Host Collection

        @Assert: Host collection is created and has random name

        """
        with self.assertRaises(CLIFactoryError):
            self._new_host_collection({'name': test_data['name']})

    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Check if host collection name can be updated

        @Feature: Host Collection

        @Assert: Host collection is created and name is updated

        """

        new_host_col = self._new_host_collection()
        # Assert that name does not matches data passed
        self.assertNotEqual(new_host_col['name'], test_data['name'])

        # Update host collection
        result = HostCollection.update({
            'id': new_host_col['id'],
            'organization-id': self.org['id'],
            'name': test_data['name']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it
        result = HostCollection.info({
            'id': new_host_col['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # Assert that name matches new value
        self.assertIsNotNone(result.stdout.get('name', None))
        self.assertEqual(result.stdout['name'], test_data['name'])
        # Assert that name does not match original value
        self.assertNotEqual(new_host_col['name'], result.stdout['name'])

    @skip_if_bug_open('bugzilla', 1171669)
    @data(
        {'description': gen_string('alpha', 15)},
        {'description': gen_string('alphanumeric', 15)},
        {'description': gen_string('numeric', 15)},
        {'description': gen_string('latin1', 15)},
        {'description': gen_string('utf8', 15)},
        {'description': gen_string('html', 15)},
    )
    def test_positive_update_2(self, test_data):
        """@Test: Check if host collection description can be updated

        @Feature: Host Collection

        @Assert: Host collection is created and description is updated

        @BZ: 1171669

        """

        new_host_col = self._new_host_collection()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_host_col['description'], test_data['description'])

        # Update sync plan
        result = HostCollection.update({
            'id': new_host_col['id'],
            'organization-id': self.org['id'],
            'description': test_data['description']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it
        result = HostCollection.info({
            'id': new_host_col['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # Assert that description matches new value
        self.assertIsNotNone(result.stdout.get('description', None))
        self.assertEqual(
            result.stdout['description'], test_data['description'])
        # Assert that description does not matches original value
        self.assertNotEqual(
            new_host_col['description'], result.stdout['description'])

    @skip_if_bug_open('bugzilla', 1245334)
    @data('3', '6', '9', '12', '15', '17', '19')
    def test_positive_update_3(self, test_data):
        """@Test: Check if host collection limits be updated

        @Feature: Host Collection

        @Assert: Host collection limits is updated

        @BZ: 1245334

        """

        new_host_col = self._new_host_collection()

        # Update sync interval
        result = HostCollection.update({
            'id': new_host_col['id'],
            'organization-id': self.org['id'],
            'max-content-hosts': test_data
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it
        result = HostCollection.info({
            'id': new_host_col['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # Assert that limit was updated
        self.assertEqual(result.stdout['limit'], test_data)
        self.assertNotEqual(
            new_host_col['limit'],
            result.stdout['limit']
        )

    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_delete_1(self, test_data):
        """@Test: Check if host collection can be created and deleted

        @Feature: Host Collection

        @Assert: Host collection is created and then deleted

        """

        new_host_col = self._new_host_collection({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(new_host_col['name'], test_data['name'])

        # Delete it
        result = HostCollection.delete(
            {'id': new_host_col['id'],
             'organization-id': self.org['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it
        result = HostCollection.info(
            {
                'id': new_host_col['id'],
            }
        )
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_add_content_host(self):
        """@Test: Check if content host can be added to host collection

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is added

        """

        host_col_name = gen_string('alpha', 15)
        content_host_name = gen_string('alpha', 15)

        try:
            new_host_col = self._new_host_collection({'name': host_col_name})
            new_system = make_content_host({
                u'name': content_host_name,
                u'organization-id': self.org['id'],
                u'content-view-id': self.default_cv['id'],
                u'lifecycle-environment-id': self.library['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        no_of_content_host = new_host_col['total-content-hosts']

        result = HostCollection.add_content_host({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
            u'content-host-ids': new_system['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(
            result.stdout['total-content-hosts'], no_of_content_host)

    def test_remove_content_host(self):
        """@Test: Check if content host can be removed from host collection

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is removed

        """

        host_col_name = gen_string('alpha', 15)
        content_host_name = gen_string('alpha', 15)

        try:
            new_host_col = self._new_host_collection({'name': host_col_name})
            new_system = make_content_host({
                u'name': content_host_name,
                u'organization-id': self.org['id'],
                u'content-view-id': self.default_cv['id'],
                u'lifecycle-environment-id': self.library['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = HostCollection.add_content_host({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
            u'content-host-ids': new_system['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })

        no_of_content_host = result.stdout['total-content-hosts']

        result = HostCollection.remove_content_host({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
            u'content-host-ids': new_system['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(
            no_of_content_host, result.stdout['total-content-hosts'])

    def test_content_hosts(self):
        """@Test: Check if content hosts added to host collection is listed

        @Feature: Host Collection

        @Assert: Content-host added to host-collection is listed

        """

        host_col_name = gen_string('alpha', 15)
        content_host_name = gen_string('alpha', 15)

        try:
            new_host_col = self._new_host_collection({'name': host_col_name})
            new_system = make_content_host({
                u'name': content_host_name,
                u'organization-id': self.org['id'],
                u'content-view-id': self.default_cv['id'],
                u'lifecycle-environment-id': self.library['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        no_of_content_host = new_host_col['total-content-hosts']
        result = HostCollection.add_content_host({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
            u'content-host-ids': new_system['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(
            result.stdout['total-content-hosts'], no_of_content_host)

        result = HostCollection.content_hosts({
            u'name': host_col_name,
            u'organization-id': self.org['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_system['id'], result.stdout[0]['id'])
