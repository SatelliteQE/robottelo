# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.factory import (
    CLIFactoryError, make_org, make_host_collection, make_content_view,
    make_lifecycle_environment, make_content_host)
from robottelo.cli.hostcollection import HostCollection
from robottelo.constants import DEFAULT_CV, ENVIRONMENT
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

    def setUp(self):
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
            TestHostCollection.library = LifecycleEnvironment.info({
                u'organization-id': TestHostCollection.org['id'],
                u'name': ENVIRONMENT,
            })
        if TestHostCollection.default_cv is None:
            TestHostCollection.default_cv = ContentView.info(
                {u'organization-id': TestHostCollection.org['id'],
                 u'name': DEFAULT_CV}
            )
        if TestHostCollection.new_cv is None:
            TestHostCollection.new_cv = make_content_view(
                {u'organization-id': TestHostCollection.org['id']}
            )
            TestHostCollection.promoted_cv = None
            cv_id = TestHostCollection.new_cv['id']
            ContentView.publish({u'id': cv_id})
            result = ContentView.version_list({u'content-view-id': cv_id})
            version_id = result[0]['id']
            ContentView.version_promote({
                u'id': version_id,
                u'organization-id': TestHostCollection.org['id'],
                u'to-lifecycle-environment-id': (
                    TestHostCollection.new_lifecycle['id']),
            })
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
        host_collection = make_host_collection({
            u'organization-id': self.org['id'],
            u'unlimited-content-hosts': unlimited,
        })
        result = HostCollection.info({
            u'id': host_collection['id'],
            u'organization-id': self.org['id'],
        })
        if unlimited in (u'True', u'Yes', 1):
            self.assertEqual(
                result['unlimited-content-hosts'], u'true')
        else:
            self.assertEqual(
                result['unlimited-content-hosts'], u'false')

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
        HostCollection.update({
            'id': new_host_col['id'],
            'name': test_data['name'],
            'organization-id': self.org['id'],
        })
        # Fetch it
        result = HostCollection.info({'id': new_host_col['id']})
        # Assert that name matches new value
        self.assertEqual(result['name'], test_data['name'])
        # Assert that name does not match original value
        self.assertNotEqual(new_host_col['name'], result['name'])

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

        """
        new_host_col = self._new_host_collection()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_host_col['description'], test_data['description'])
        # Update sync plan
        HostCollection.update({
            'description': test_data['description'],
            'id': new_host_col['id'],
            'organization-id': self.org['id'],
        })
        # Fetch it
        result = HostCollection.info({'id': new_host_col['id']})
        # Assert that description matches new value
        self.assertEqual(result['description'], test_data['description'])
        # Assert that description does not matches original value
        self.assertNotEqual(new_host_col['description'], result['description'])

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
        HostCollection.update({
            'id': new_host_col['id'],
            'max-content-hosts': test_data,
            'organization-id': self.org['id'],
        })
        # Fetch it
        result = HostCollection.info({'id': new_host_col['id']})
        # Assert that limit was updated
        self.assertEqual(result['limit'], test_data)
        self.assertNotEqual(new_host_col['limit'], result['limit'])

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
        HostCollection.delete({
            'id': new_host_col['id'],
            'organization-id': self.org['id'],
        })
        # Fetch it
        with self.assertRaises(CLIReturnCodeError):
            HostCollection.info({'id': new_host_col['id']})

    def test_add_content_host(self):
        """@Test: Check if content host can be added to host collection

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is added

        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        no_of_content_host = new_host_col['total-content-hosts']
        HostCollection.add_content_host({
            u'content-host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-content-hosts'], no_of_content_host)

    def test_remove_content_host(self):
        """@Test: Check if content host can be removed from host collection

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is removed

        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        HostCollection.add_content_host({
            u'content-host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        no_of_content_host = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })['total-content-hosts']
        HostCollection.remove_content_host({
            u'content-host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        self.assertGreater(no_of_content_host, result['total-content-hosts'])

    def test_content_hosts(self):
        """@Test: Check if content hosts added to host collection is listed

        @Feature: Host Collection

        @Assert: Content-host added to host-collection is listed

        """
        host_col_name = gen_string('alpha', 15)
        new_host_col = self._new_host_collection({'name': host_col_name})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        no_of_content_host = new_host_col['total-content-hosts']
        HostCollection.add_content_host({
            u'content-host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-content-hosts'], no_of_content_host)
        result = HostCollection.content_hosts({
            u'name': host_col_name,
            u'organization-id': self.org['id']
        })
        self.assertEqual(new_system['id'], result[0]['id'])
