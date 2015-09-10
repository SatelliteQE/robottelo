# -*- encoding: utf-8 -*-
"""Test class for Host CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    make_lifecycle_environment, make_org, CLIFactoryError)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.decorators import data, run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestLifeCycleEnvironment(CLITestCase):
    """Test class for Lifecycle Environment CLI"""

    org = None

    def setUp(self):  # noqa
        """Tests for Lifecycle Environment via Hammer CLI"""

        super(TestLifeCycleEnvironment, self).setUp()

        if TestLifeCycleEnvironment.org is None:
            TestLifeCycleEnvironment.org = make_org()

    # Issues validation
    def test_bugzilla_1077386(self):
        """@Test: List subcommand returns standard output

        @Feature: Lifecycle Environment

        @Assert: There should not be an error returned

        """

        # List avaialble lifecycle environments using default Table
        # output
        cmd = u"lifecycle-environment list --organization-id=\"%s\""
        result = LifecycleEnvironment.execute(
            cmd % self.org['id'],
            None,
            None,
            False
        )

        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(len(result.stdout), 0)

    def test_bugzilla_1077333(self):
        """@Test: Search lifecycle environment via its name containing UTF-8 chars

        @Feature: Lifecycle Environment

        @Assert: Can get info for lifecycle by its name

        """
        data = {
            'organization-id': self.org['id'],
            'name': gen_string('utf8', 15),
        }

        # Can we find the new object
        result = LifecycleEnvironment.info({
            'organization-id': self.org['id'],
            'name': make_lifecycle_environment(data)['name'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['name'], data['name'])

    # CRUD
    @data(
        {'name': gen_string("alpha", 15)},
        {'name': gen_string("alphanumeric", 15)},
        {'name': gen_string("numeric", 15)},
        {'name': gen_string("latin1", 15)},
        {'name': gen_string("utf8", 15)},
        {'name': gen_string("html", 15)},
    )
    def test_positive_create_1(self, test_data):
        """@Test: Create lifecycle environment with valid name, prior to Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created with Library as prior

        """
        lifecycle_environment = make_lifecycle_environment({
            'organization-id': self.org['id'],
            'name': test_data['name'],
        })

        self.assertEqual(
            lifecycle_environment['prior-lifecycle-environment'], u'Library')

    @data(
        {'name': gen_string("alpha", 15)},
        {'name': gen_string("alphanumeric", 15)},
        {'name': gen_string("numeric", 15)},
        {'name': gen_string("latin1", 15)},
        {'name': gen_string("utf8", 15)},
        {'name': gen_string("html", 15)},
    )
    def test_positive_create_2(self, test_data):
        """@Test: Create lifecycle environment with valid name and description,
        prior to Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created with Library as prior

        """
        description = test_data['name']

        lifecycle_environment = make_lifecycle_environment({
            'organization-id': self.org['id'],
            'name': test_data['name'],
            'description': description,
        })

        self.assertEqual(lifecycle_environment['name'], test_data['name'])
        self.assertEqual(
            lifecycle_environment['description'], description)
        self.assertEqual(
            lifecycle_environment['prior-lifecycle-environment'], u'Library')

    @data(
        {'label': gen_string("alpha", 15)},
        {'label': gen_string("alphanumeric", 15)},
        {'label': gen_string("numeric", 15)},
    )
    def test_create_lifecycle_environment_by_label(self, test_data):
        """@Test: Create lifecycle environment with valid name and label

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment with label is created

        """
        try:
            new_le = make_lifecycle_environment({
                'organization-id': self.org['id'],
                'name': test_data['label'],
                'label': test_data['label'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(new_le['label'], test_data['label'])

    def test_create_lifecycle_environment_by_organization_name(self):
        """@Test: Create lifecycle environment, specifying organization name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        try:
            new_le = make_lifecycle_environment({
                'organization': self.org['name'],
                'name': gen_string('alpha'),
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(new_le['organization'], self.org['name'])

    def test_create_lifecycle_environment_by_organization_label(self):
        """@Test: Create lifecycle environment, specifying organization name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        try:
            new_le = make_lifecycle_environment({
                'organization-label': self.org['label'],
                'name': gen_string('alpha'),
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(new_le['organization'], self.org['name'])

    @data(
        {'name': gen_string("alpha", 15)},
        {'name': gen_string("alphanumeric", 15)},
        {'name': gen_string("numeric", 15)},
        {'name': gen_string("latin1", 15)},
        {'name': gen_string("utf8", 15)},
        {'name': gen_string("html", 15)},
    )
    def test_positive_delete_1(self, test_data):
        """@Test: Create lifecycle environment with valid name, prior to Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is deleted

        """
        new_obj = make_lifecycle_environment({
            'organization-id': self.org['id'],
            'name': test_data['name'],
        })

        # Delete the lifecycle environment
        result = LifecycleEnvironment.delete({'id': new_obj['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Can we find the object
        result = LifecycleEnvironment.info({
            'organization-id': self.org['id'],
            'id': new_obj['id'],
        })
        self.assertGreater(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data(
        {'name': gen_string("alpha", 15)},
        {'name': gen_string("alphanumeric", 15)},
        {'name': gen_string("numeric", 15)},
        {'name': gen_string("latin1", 15)},
        {'name': gen_string("utf8", 15)},
        {'name': gen_string("html", 15)},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Create lifecycle environment then update its name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment name is updated

        """
        new_obj = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })

        # Update its name
        result = LifecycleEnvironment.update({
            'id': new_obj['id'],
            'new-name': test_data['name'],
            'organization-id': self.org['id'],
            'prior': new_obj['prior-lifecycle-environment'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch the object
        result = LifecycleEnvironment.info({
            'id': new_obj['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(len(result.stdout), 0)
        self.assertEqual(test_data['name'], result.stdout['name'])
        self.assertNotEqual(new_obj['name'], result.stdout['name'])

    @data(
        {'description': gen_string("alpha", 15)},
        {'description': gen_string("alphanumeric", 15)},
        {'description': gen_string("numeric", 15)},
        {'description': gen_string("latin1", 15)},
        {'description': gen_string("utf8", 15)},
        {'description': gen_string("html", 15)},
    )
    def test_positive_update_2(self, test_data):
        """@Test: Create lifecycle environment then update its description

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment description is updated

        """
        new_obj = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })

        # Update its description
        result = LifecycleEnvironment.update({
            'description': test_data['description'],
            'id': new_obj['id'],
            'organization-id': self.org['id'],
            'prior': new_obj['prior-lifecycle-environment'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch the object
        result = LifecycleEnvironment.info({
            'id': new_obj['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(len(result.stdout), 0)
        self.assertEqual(
            test_data['description'], result.stdout['description'])
        self.assertNotEqual(
            new_obj['description'], result.stdout['description'])

    def test_environment_paths(self):
        """@Test: List the environment paths under a given organization

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment paths listed

        """
        try:
            org = make_org()
            test_env = make_lifecycle_environment({
                'organization-id': org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Add paths to lifecycle environments
        result = LifecycleEnvironment.paths({
            'organization-id': org['id'],
            'permission-type': 'readable',
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertIn(
            u'Library >> {0}'.format(test_env['name']),
            u''.join(result.stdout)
        )
