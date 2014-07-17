# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

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
from robottelo.common.decorators import data, skip_if_bz_bug_open
from robottelo.common.helpers import generate_string
from robottelo.test import CLITestCase


@ddt
class TestContentHost(CLITestCase):
    """
    content-host CLI tests.
    """

    NEW_ORG = None
    NEW_CW = None
    PROMOTED_CW = None
    NEW_LIFECYCLE = None
    LIBRARY = None
    DEFAULT_CV = None

    def setUp(self):
        """
        Tests for Content Host via Hammer CLI
        """

        super(TestContentHost, self).setUp()

        if TestContentHost.NEW_ORG is None:
            TestContentHost.NEW_ORG = make_org()
        if TestContentHost.NEW_LIFECYCLE is None:
            TestContentHost.NEW_LIFECYCLE = make_lifecycle_environment(
                {u'organization-id': TestContentHost.NEW_ORG['id']}
            )
        if TestContentHost.LIBRARY is None:
            library_result = LifecycleEnvironment.info(
                {u'organization-id': TestContentHost.NEW_ORG['id'],
                 u'name': u'Library'}
            )
            TestContentHost.LIBRARY = library_result.stdout
        if TestContentHost.DEFAULT_CV is None:
            cv_result = ContentView.info(
                {u'organization-id': TestContentHost.NEW_ORG['id'],
                 u'name': u'Default Organization View'}
            )
            TestContentHost.DEFAULT_CV = cv_result.stdout
        if TestContentHost.NEW_CW is None:
            TestContentHost.NEW_CW = make_content_view(
                {u'organization-id': TestContentHost.NEW_ORG['id']}
            )
            TestContentHost.PROMOTED_CW = None
            cw_id = TestContentHost.NEW_CW['id']
            ContentView.publish({u'id': cw_id})
            result = ContentView.version_list({u'content-view-id': cw_id})
            version_id = result.stdout[0]['id']
            promotion = ContentView.version_promote({
                u'id': version_id,
                u'environment-id': TestContentHost.NEW_LIFECYCLE['id'],
                u'organization-id': TestContentHost.NEW_ORG['id']
            })
            if promotion.stderr == []:
                TestContentHost.PROMOTED_CW = TestContentHost.NEW_CW

    @data(
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
        {u'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if content host can be created with random names
        @Feature: Content Hosts
        @Assert: Content host is created and has random name
        """

        new_system = make_content_host({
            u'name': test_data['name'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {u'description': generate_string('alpha', 15)},
        {u'description': generate_string('alphanumeric', 15)},
        {u'description': generate_string('numeric', 15)},
        {u'description': generate_string('latin1', 15)},
        {u'description': generate_string('utf8', 15)},
        {u'description': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if content host can be created with random description
        @Feature: Content Hosts
        @Assert: Content host is created and has random description
        """

        new_system = make_content_host({
            u'description': test_data['description'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that description matches data passed
        self.assertEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @attr('cli', 'content-host')
    def test_positive_create_3(self):
        """
        @Test: Check if content host can be created with organization name
        @Feature: Content Hosts
        @Assert: Content host is created using organization name
        """

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization': self.NEW_ORG['name'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Info does not tell us information about the organization so
        # let's assert that content view and environments match instead
        self.assertEqual(
            new_system['content-view'],
            self.DEFAULT_CV['name'],
            "Content views don't match")
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
            "Environments don't match")

    @attr('cli', 'content-host')
    def test_positive_create_4(self):
        """
        @Test: Check if content host can be created with organization label
        @Feature: Content Hosts
        @Assert: Content host is created using organization label
        """

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization-label': self.NEW_ORG['label'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Info does not tell us information about the organization so
        # let's assert that content view and environments match instead
        self.assertEqual(
            new_system['content-view'],
            self.DEFAULT_CV['name'],
            "Content views don't match")
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
            "Environments don't match")

    @attr('cli', 'content-host')
    def test_positive_create_5(self):
        """
        @Test: Check if content host can be created with content view name
        @Feature: Content Hosts
        @Assert: Content host is created using content view name
        """

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view': self.DEFAULT_CV['name'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['content-view'],
            self.DEFAULT_CV['name'],
            "Content views don't match"
        )

    @skip_if_bz_bug_open('1107319')
    @attr('cli', 'content-host')
    def test_positive_create_6(self):
        """
        @Test: Check if content host can be created with lifecycle name
        @Feature: Content Hosts
        @Assert: Content host is created using lifecycle name
        """

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment': self.LIBRARY['name']})
        # Assert that lifecycles matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
            "Lifecycle environments don't match"
        )

    @skip_if_bz_bug_open(1114046)
    @attr('cli', 'content-host')
    def test_positive_create_7(self):
        """
        @Test: Check if content host can be created with new lifecycle
        @Feature: Content Hosts
        @Assert: Content host is created using new lifecycle
        @BZ: 1114046
        """

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.NEW_LIFECYCLE['id']})
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.NEW_LIFECYCLE['name'],
            "Environments don't match"
        )

    @attr('cli', 'content-host')
    def test_positive_create_8(self):
        """
        @Test: Check if content host can be created with new content view
        @Feature: Content Hosts
        @Assert: Content host is created using new published, promoted content view
        """

        if TestContentHost.PROMOTED_CW is None:
            self.fail("Couldn't prepare promoted contentview for this test")

        new_system = make_content_host({
            u'name': generate_string('alpha', 15),
            u'organization-id': TestContentHost.NEW_ORG['id'],
            u'content-view-id': TestContentHost.PROMOTED_CW['id'],
            u'environment-id': TestContentHost.NEW_LIFECYCLE['id']})
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['content-view'],
            TestContentHost.PROMOTED_CW['name'],
            "Content Views don't match"
        )

    @data(
        {u'name': generate_string('alpha', 300)},
        {u'name': generate_string('alphanumeric', 300)},
        {u'name': generate_string('numeric', 300)},
        {u'name': generate_string('latin1', 300)},
        {u'name': generate_string('utf8', 300)},
        {u'name': generate_string('html', 300)},
    )
    @attr('cli', 'content-host')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if content host can be created with random long names
        @Feature: Content Hosts
        @Assert: Content host is not created
        """

        with self.assertRaises(Exception):
            make_content_host({
                u'name': test_data['name'],
                u'organization-id': self.NEW_ORG['id'],
                u'content-view-id': self.DEFAULT_CV['id'],
                u'environment-id': self.LIBRARY['id']})

    @data(
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
        {u'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if content host name can be updated
        @Feature: Content Hosts
        @Assert: Content host is created and name is updated
        """

        new_system = make_content_host({
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that name does not matches data passed
        self.assertNotEqual(
            new_system['name'],
            test_data['name'],
            "Names should not match"
        )

        # Update system group
        result = ContentHost.update({
            u'id': new_system['id'],
            u'name': test_data['name']})
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info({
            u'id': new_system['id']})
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
        {u'description': generate_string('alpha', 15)},
        {u'description': generate_string('alphanumeric', 15)},
        {u'description': generate_string('numeric', 15)},
        {u'description': generate_string('latin1', 15)},
        {u'description': generate_string('utf8', 15)},
        {u'description': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if content host description can be updated
        @Feature: Content Hosts
        @Assert: Content host is created and description is updated
        @BZ: 1082157
        """

        new_system = make_content_host({
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions should not match"
        )

        # Update sync plan
        result = ContentHost.update({
            u'id': new_system['id'],
            u'description': test_data['description']})
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info({
            u'id': new_system['id']})
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
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
        {u'name': generate_string('html', 15)},
    )
    @attr('cli', 'content-host')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if content host can be created and deleted
        @Feature: Content Hosts
        @Assert: Content host is created and then deleted
        """

        new_system = make_content_host({
            u'name': test_data['name'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'environment-id': self.LIBRARY['id']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = ContentHost.delete({u'id': new_system['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content host was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = ContentHost.info({
            u'id': new_system['id']})
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

