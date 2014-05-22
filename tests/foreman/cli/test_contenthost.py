# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Content-Host CLI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.cli.factory import (
    make_org, make_content_view, make_lifecycle_environment,
    make_content_host)
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


@ddt
class TestContentHost(BaseCLI):
    """
    content-host CLI tests.
    """

    org = None
    environment = None
    content_view = None

    def setUp(self):
        """
        Tests for Content Host via Hammer CLI
        """

        super(TestContentHost, self).setUp()

        if TestContentHost.org is None:
            TestContentHost.org = make_org()
        if TestContentHost.environment is None:
            TestContentHost.environment = make_lifecycle_environment(
                {u'organization-id': TestContentHost.org['id']}
            )
        if TestContentHost.content_view is None:
            TestContentHost.content_view = make_content_view(
                {u'organization-id': TestContentHost.org['id']}
            )

    def _new_content_host(self, options=None):
        """
        Make a new content host and asserts its success
        """

        if options is None:
            options = {}

        # Use default organization if None are provided
        if not options.get('organization-id', None):
            options['organization-id'] = self.org['id']

        # If no environment id, use organization's 'Library'
        if not options.get('environment-id', None):
            library_result = LifecycleEnvironment.info(
                {'organization-id': self.org['id'],
                 'name': 'Library'}
            )
            self.assertEqual(
                library_result.return_code,
                0,
                "Could not find Library environment for org: %s" %
                options['organization-id']
            )
            self.assertEqual(
                len(library_result.stderr),
                0,
                "There should not be an error here"
            )
            options['environment-id'] = library_result.stdout['id']

        # Use Default Organization View if none are provided
        # Until we can look up content view by name, we need to list
        # them and locate the ID for 'Default Organization View'
        if not options.get('content-view-id', None):
            all_cvs = ContentView.list(
                {'organization-id': self.org['id'], 'per-page': False})
            self.assertEqual(
                all_cvs.return_code,
                0,
                "Could not fetch Content Views for org: %s" %
                options['organization-id'])
            self.assertEqual(
                len(all_cvs.stderr),
                0,
                "Error while fetching content views for org: %s" %
                options['organization-id'])
            for contentview in all_cvs.stdout:
                if contentview['name'] == 'Default Organization View':
                    options['content-view-id'] = contentview['content-view-id']

        content_host = make_content_host(options)

        # Fetch it
        result = ContentHost.info(
            {
                'id': content_host['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Content host was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Return the content host dictionary
        return content_host

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if content host can be created with random names
        @Feature: Content Hosts
        @Assert: Content host is created and has random name
        """

        new_system = self._new_content_host({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
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
    @attr('cli', 'content-host')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if content host can be created with random description
        @Feature: Content Hosts
        @Assert: Content host is created and has random description
        """

        new_system = self._new_content_host(
            {'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'content-host')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if content host can be created with random names
        @Feature: Content Hosts
        @Assert: Content host is not created
        """

        with self.assertRaises(Exception):
            self._new_content_host({'name': test_data['name']})

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if content host name can be updated
        @Feature: Content Hosts
        @Assert: Content host is created and name is updated
        """

        new_system = self._new_content_host()
        # Assert that name does not matches data passed
        self.assertNotEqual(
            new_system['name'],
            test_data['name'],
            "Names should not match"
        )

        # Update system group
        result = ContentHost.update(
            {
                'id': new_system['id'],
                'name': test_data['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
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
            new_system['name'],
            result.stdout['name'],
            "Names should not match"
        )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if content host description can be updated
        @Feature: Content Hosts
        @Assert: Content host is created and description is updated
        @BZ: 1082157
        """

        new_system = self._new_content_host()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions should not match"
        )

        # Update sync plan
        result = ContentHost.update(
            {
                'id': new_system['id'],
                'description': test_data['description']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
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
            new_system['description'],
            result.stdout['description'],
            "Descriptions should not match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if content host can be created and deleted
        @Feature: Content Hosts
        @Assert: Content host is created and then deleted
        """

        new_system = self._new_content_host({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = ContentHost.delete({'id': new_system['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "Content host should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )
