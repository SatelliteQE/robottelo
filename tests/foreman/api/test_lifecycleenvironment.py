"""Unit tests for the ``environments`` paths.

Documentation for these paths is available here:
http://www.katello.org/docs/api/apidoc/lifecycle_environments.html

"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on
from robottelo.test import APITestCase


class LifecycleEnvironmentTestCase(APITestCase):
    """Tests for ``katello/api/v2/environments``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(LifecycleEnvironmentTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @run_only_on('sat')
    def test_positive_create_different_names(self):
        """@Test: Create lifecycle environment with valid name only

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created and has proper name

        """
        for name in valid_data_list():
            with self.subTest(name):
                lc_env = entities.LifecycleEnvironment(
                    organization=self.org,
                    name=name,
                ).create()
                self.assertEqual(lc_env.name, name)

    @run_only_on('sat')
    def test_positive_create_description(self):
        """@Test: Create lifecycle environment with valid description

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created and has proper description

        """
        description = gen_string('utf8')
        lc_env = entities.LifecycleEnvironment(
            organization=self.org,
            description=description,
        ).create()
        self.assertEqual(lc_env.description, description)

    @run_only_on('sat')
    def test_positive_create_prior(self):
        """@Test: Create lifecycle environment with valid name, prior to
        Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created with Library as prior

        """
        lc_env = entities.LifecycleEnvironment(
            organization=self.org,
        ).create()
        self.assertEqual(lc_env.prior.read().name, ENVIRONMENT)

    @run_only_on('sat')
    def test_negative_create_different_names(self):
        """@Test: Create lifecycle environment providing an invalid name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.LifecycleEnvironment(name=name).create()

    @run_only_on('sat')
    def test_positive_update_different_names(self):
        """@Test: Create lifecycle environment providing the initial name, then
        update its name to another valid name.

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created and updated properly

        """
        lc_env = entities.LifecycleEnvironment(organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                lc_env = entities.LifecycleEnvironment(
                    id=lc_env.id, name=new_name).update(['name'])
                self.assertEqual(lc_env.name, new_name)

    @run_only_on('sat')
    def test_positive_update_description(self):
        """@Test: Create lifecycle environment providing the initial
        description, then update its description to another one.

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created and updated properly

        """
        lc_env = entities.LifecycleEnvironment(
            organization=self.org,
            description=gen_string('alpha'),
        ).create()
        new_description = gen_string('utf8')
        lc_env = entities.LifecycleEnvironment(
            id=lc_env.id, description=new_description).update(['description'])
        self.assertEqual(lc_env.description, new_description)

    @run_only_on('sat')
    def test_negative_update_different_names(self):
        """@Test: Update lifecycle environment providing an invalid name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is not updated and corresponding error
        is raised

        """
        name = gen_string('alpha')
        lc_env = entities.LifecycleEnvironment(
            organization=self.org,
            name=name,
        ).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.LifecycleEnvironment(
                        id=lc_env.id, name=new_name).update(['name'])
                    self.assertEqual(lc_env.read().name, name)

    @run_only_on('sat')
    def test_positive_delete(self):
        """@Test: Create lifecycle environment and then delete it.

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is deleted successfully

        """
        lc_env = entities.LifecycleEnvironment(organization=self.org).create()
        lc_env.delete()
        with self.assertRaises(HTTPError):
            lc_env.read()

    @run_only_on('sat')
    def test_get_all(self):
        """@Test: Search for a lifecycle environment and specify an org ID.

        @Feature: Lifecycle Environment

        @Steps:

        1. Create an organization.
        2. Create a lifecycle environment belonging to the organization.
        3. Search for lifecycle environments in the organization.

        @Assert: Only "Library" and the lifecycle environment just created are
        in the search results.

        """
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        lc_envs = lc_env.search({'organization'})
        self.assertEqual(len(lc_envs), 2)
        self.assertEqual(
            {lc_env_.name for lc_env_ in lc_envs},
            {u'Library', lc_env.name},
        )
