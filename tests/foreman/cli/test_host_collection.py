# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host Collection CLI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.factory import (CLIFactoryError,
                                   make_org,
                                   make_host_collection,
                                   make_content_view,
                                   make_lifecycle_environment,
                                   make_content_host)
from robottelo.cli.hostcollection import HostCollection
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_string
from robottelo.test import CLITestCase


@ddt
class TestHostCollection(CLITestCase):
    """
    Host Collection CLI tests.
    """

    org = None
    NEW_CV = None
    PROMOTED_CV = None
    NEW_LIFECYCLE = None
    LIBRARY = None
    DEFAULT_CV = None

    def setUp(self):
        """
        Tests for Host Collections via Hammer CLI
        """

        super(TestHostCollection, self).setUp()

        if TestHostCollection.org is None:
            TestHostCollection.org = make_org()
        if TestHostCollection.NEW_LIFECYCLE is None:
            TestHostCollection.NEW_LIFECYCLE = make_lifecycle_environment(
                {u'organization-id': TestHostCollection.org['id']}
            )
        if TestHostCollection.LIBRARY is None:
            library_result = LifecycleEnvironment.info(
                {u'organization-id': TestHostCollection.org['id'],
                 u'name': u'Library'}
            )
            TestHostCollection.LIBRARY = library_result.stdout
        if TestHostCollection.DEFAULT_CV is None:
            cv_result = ContentView.info(
                {u'organization-id': TestHostCollection.org['id'],
                 u'name': u'Default Organization View'}
            )
            TestHostCollection.DEFAULT_CV = cv_result.stdout
        if TestHostCollection.NEW_CV is None:
            TestHostCollection.NEW_CV = make_content_view(
                {u'organization-id': TestHostCollection.org['id']}
            )
            TestHostCollection.PROMOTED_CV = None
            cv_id = TestHostCollection.NEW_CV['id']
            ContentView.publish({u'id': cv_id})
            result = ContentView.version_list({u'content-view-id': cv_id})
            version_id = result.stdout[0]['id']
            promotion = ContentView.version_promote({
                u'id': version_id,
                u'lifecycle-environment-id': TestHostCollection.NEW_LIFECYCLE[
                    'id'],
                u'organization-id': TestHostCollection.org['id']
            })
            if promotion.stderr == []:
                TestHostCollection.PROMOTED_CV = TestHostCollection.NEW_CV

    def _new_host_collection(self, options=None):
        """
        Make a host collection and asserts its success
        """

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options['organization-id'] = self.org['id']

        group = make_host_collection(options)

        # Fetch it
        result = HostCollection.info(
            {
                'id': group['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Return the host collection dictionary
        return group

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'hostcollection')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if host collection can be created with random names
        @Feature: Host Collection
        @Assert: Host collection is created and has random name
        """

        new_host_col = self._new_host_collection({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_host_col['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'hostcollection')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if host collection can be created with random description
        @Feature: Host Collection
        @Assert: Host collection is created and has random description
        """

        new_host_col = self._new_host_collection(
            {'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_host_col['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data('1', '3', '5', '10', '20')
    @attr('cli', 'hostcollection')
    def test_positive_create_3(self, test_data):
        """
        @Test: Check if host collection can be created with random limits
        @Feature: Host Collection
        @Assert: Host collection is created and has random limits
        """

        new_host_col = self._new_host_collection(
            {'max-content-hosts': test_data})
        # Assert that limit matches data passed
        self.assertEqual(
            new_host_col['max-content-hosts'],
            str(test_data),
            ("Limits don't match '%s' != '%s'" %
             (new_host_col['max-content-hosts'], str(test_data)))
        )

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'hostcollection')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if host collection can be created with random names
        @Feature: Host Collection
        @Assert: Host collection is created and has random name
        """

        with self.assertRaises(Exception):
            self._new_host_collection({'name': test_data['name']})

    @skip_if_bug_open('bugzilla', 1084240)
    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'hostcollection')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if host collection name can be updated
        @Feature: Host Collection
        @Assert: Host collection is created and name is updated
        @BZ: 1084240
        """

        new_host_col = self._new_host_collection()
        # Assert that name does not matches data passed
        self.assertNotEqual(
            new_host_col['name'],
            test_data['name'],
            "Names should not match"
        )

        # Update host collection
        result = HostCollection.update(
            {
                'id': new_host_col['id'],
                'organization-id': self.org['id'],
                'name': test_data['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = HostCollection.info(
            {
                'id': new_host_col['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that name matches new value
        self.assertIsNotNone(
            result.stdout.get('name', None),
            "The name field was not returned"
        )
        self.assertEqual(
            result.stdout['name'],
            test_data['name'],
            "Names should match"
        )
        # Assert that name does not match original value
        self.assertNotEqual(
            new_host_col['name'],
            result.stdout['name'],
            "Names should not match"
        )

    @skip_if_bug_open('bugzilla', 1084240)
    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'hostcollection')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if host collection description can be updated
        @Feature: Host Collection
        @Assert: Host collection is created and description is updated
        @BZ: 1084240
        """

        new_host_col = self._new_host_collection()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_host_col['description'],
            test_data['description'],
            "Descriptions should not match"
        )

        # Update sync plan
        result = HostCollection.update(
            {
                'id': new_host_col['id'],
                'organization-id': self.org['id'],
                'description': test_data['description']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = HostCollection.info(
            {
                'id': new_host_col['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that description matches new value
        self.assertIsNotNone(
            result.stdout.get('description', None),
            "The description field was not returned"
        )
        self.assertEqual(
            result.stdout['description'],
            test_data['description'],
            "Descriptions should match"
        )
        # Assert that description does not matches original value
        self.assertNotEqual(
            new_host_col['description'],
            result.stdout['description'],
            "Descriptions should not match"
        )

    @skip_if_bug_open('bugzilla', 1084240)
    @data('3', '6', '9', '12', '15', '17', '19')
    @attr('cli', 'hostcollection')
    def test_positive_update_3(self, test_data):
        """
        @Test: Check if host collection limits be updated
        @Feature: Host Collection
        @Assert: Host collection limits is updated
        @BZ: 1084240
        """

        new_host_col = self._new_host_collection()

        # Update sync interval
        result = HostCollection.update(
            {
                'id': new_host_col['id'],
                'organization-id': self.org['id'],
                'max-content-hosts': test_data
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = HostCollection.info(
            {
                'id': new_host_col['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that limit was updated
        self.assertEqual(
            result.stdout['max-content-hosts'],
            test_data,
            "Limits don't match"
        )
        self.assertNotEqual(
            new_host_col['max-content-hosts'],
            result.stdout['max-content-hosts'],
            "Limits don't match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'hostcollection')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if host collection can be created and deleted
        @Feature: Host Collection
        @Assert: Host collection is created and then deleted
        """

        new_host_col = self._new_host_collection({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_host_col['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = HostCollection.delete(
            {'id': new_host_col['id'],
             'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Host collection was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = HostCollection.info(
            {
                'id': new_host_col['id'],
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "Host collection should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )

    def test_add_content_host(self):
        """
        @Test: Check if content host can be added to host collection
        @Feature: Host Collection
        @Assert: Host collection is created and content-host is added
        """

        host_col_name = generate_string('alpha', 15)
        content_host_name = generate_string('alpha', 15)

        try:
            new_host_col = self._new_host_collection({'name': host_col_name})
            new_system = make_content_host({u'name': content_host_name,
                                            u'organization-id': self.org['id'],
                                            u'content-view-id':
                                            self.DEFAULT_CV['id'],
                                            u'lifecycle-environment-id':
                                            self.LIBRARY['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = HostCollection.add_content_host(
            {'id': new_host_col['id'],
                'organization-id': self.org['id'],
                'content-host-ids': new_system['id']})
        self.assertEqual(result.return_code, 0,
                         "Content Host not added to host collection")
        self.assertEqual(len(result.stderr), 0,
                         "No error was expected")

    def test_remove_content_host(self):
        """
        @Test: Check if content host can be removed from host collection
        @Feature: Host Collection
        @Assert: Host collection is created and content-host is removed
        """

        host_col_name = generate_string('alpha', 15)
        content_host_name = generate_string('alpha', 15)

        try:
            new_host_col = self._new_host_collection({'name': host_col_name})
            new_system = make_content_host({u'name': content_host_name,
                                            u'organization-id': self.org['id'],
                                            u'content-view-id':
                                            self.DEFAULT_CV['id'],
                                            u'lifecycle-environment-id':
                                            self.LIBRARY['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = HostCollection.add_content_host(
            {'id': new_host_col['id'],
             'organization-id': self.org['id'],
             'content-host-ids': new_system['id']})
        self.assertEqual(result.return_code, 0,
                         "Content Host not added to host collection")
        self.assertEqual(len(result.stderr), 0,
                         "No error was expected")

        result = HostCollection.remove_content_host(
            {'id': new_host_col['id'],
             'organization-id': self.org['id'],
             'content-host-ids': new_system['id']})
        self.assertEqual(result.return_code, 0,
                         "Content Host not removed host collection")
        self.assertEqual(len(result.stderr), 0,
                         "No error was expected")
