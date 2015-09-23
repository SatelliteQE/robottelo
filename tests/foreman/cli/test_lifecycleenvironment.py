# -*- encoding: utf-8 -*-
"""Test class for Host CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_lifecycle_environment, make_org
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import ENVIRONMENT
from robottelo.decorators import data, run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestLifeCycleEnvironment(CLITestCase):
    """Test class for Lifecycle Environment CLI"""

    org = None

    def setUp(self):
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

        # List available lifecycle environments using default Table
        # output
        cmd = u'lifecycle-environment list --organization-id="%s"'
        result = LifecycleEnvironment.execute(
            cmd % self.org['id'],
            None,
            None,
            False,
        )
        self.assertGreater(len(result), 0)

    def test_bugzilla_1077333(self):
        """@Test: Search lifecycle environment via its name containing UTF-8 chars

        @Feature: Lifecycle Environment

        @Assert: Can get info for lifecycle by its name

        """
        test_data = {
            'name': gen_string('utf8', 15),
            'organization-id': self.org['id'],
        }
        # Can we find the new object
        result = LifecycleEnvironment.info({
            'name': make_lifecycle_environment(test_data)['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result['name'], test_data['name'])

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
            'name': test_data['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            lifecycle_environment['prior-lifecycle-environment'], ENVIRONMENT)

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
            'description': description,
            'name': test_data['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(lifecycle_environment['name'], test_data['name'])
        self.assertEqual(
            lifecycle_environment['description'], description)
        self.assertEqual(
            lifecycle_environment['prior-lifecycle-environment'], ENVIRONMENT)

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
        new_le = make_lifecycle_environment({
            'label': test_data['label'],
            'name': test_data['label'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(new_le['label'], test_data['label'])

    def test_create_lifecycle_environment_by_organization_name(self):
        """@Test: Create lifecycle environment, specifying organization name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        new_le = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization': self.org['name'],
        })
        self.assertEqual(new_le['organization'], self.org['name'])

    def test_create_lifecycle_environment_by_organization_label(self):
        """@Test: Create lifecycle environment, specifying organization label

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        new_le = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization-label': self.org['label'],
        })
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
        new_le = make_lifecycle_environment({
            'name': test_data['name'],
            'organization-id': self.org['id'],
        })
        # Delete the lifecycle environment
        LifecycleEnvironment.delete({'id': new_le['id']})
        # Can we find the object
        with self.assertRaises(CLIReturnCodeError):
            LifecycleEnvironment.info({
                'id': new_le['id'],
                'organization-id': self.org['id'],
            })

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
        new_le = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        # Update its name
        LifecycleEnvironment.update({
            'id': new_le['id'],
            'new-name': test_data['name'],
            'organization-id': self.org['id'],
            'prior': new_le['prior-lifecycle-environment'],
        })
        # Fetch the object
        result = LifecycleEnvironment.info({
            'id': new_le['id'],
            'organization-id': self.org['id'],
        })
        self.assertGreater(len(result), 0)
        self.assertEqual(test_data['name'], result['name'])
        self.assertNotEqual(new_le['name'], result['name'])

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
        new_le = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        # Update its description
        LifecycleEnvironment.update({
            'description': test_data['description'],
            'id': new_le['id'],
            'organization-id': self.org['id'],
            'prior': new_le['prior-lifecycle-environment'],
        })
        # Fetch the object
        result = LifecycleEnvironment.info({
            'id': new_le['id'],
            'organization-id': self.org['id'],
        })
        self.assertGreater(len(result), 0)
        self.assertEqual(test_data['description'], result['description'])
        self.assertNotEqual(new_le['description'], result['description'])

    def test_environment_paths(self):
        """@Test: List the environment paths under a given organization

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment paths listed

        """
        org = make_org()
        test_env = make_lifecycle_environment({
            'organization-id': org['id'],
        })
        # Add paths to lifecycle environments
        result = LifecycleEnvironment.paths({
            'organization-id': org['id'],
            'permission-type': 'readable',
        })
        self.assertIn(
            u'Library >> {0}'.format(test_env['name']),
            u''.join(result)
        )
