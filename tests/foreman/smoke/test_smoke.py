# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Repository CLI
"""

from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.cli.factory import make_user
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.contentview import ContentView
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.user import User
from robottelo.test import CLITestCase


@ddt
class TestSmoke(CLITestCase):
    """Smoke tests for a brand new Satellite installation"""

    org = None
    product = None

    def test_find_default_org(self):
        """
        @Test: Check if Default_Organization is present
        @Feature: Smoke Test
        @Assert: Default_Organization is found
        """

        result = Org.info({'name': 'Default_Organization'})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code)
        )
        self.assertEqual(
            len(result.stderr),
            0,
            "There was an error fetching the default org: {0}".format(
                result.stderr)
        )
        self.assertEqual(
            result.stdout['name'],
            'Default_Organization',
            "Could not find the Default_Organization"
        )

    def test_find_default_location(self):
        """
        @Test: Check if Default_Location is present
        @Feature: Smoke Test
        @Assert: Default_Location is found
        """

        result = Location.info({'name': 'Default_Location'})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code)
        )
        self.assertEqual(
            len(result.stderr),
            0,
            "There was an error fetching the default location: {0}".format(
                result.stderr)
        )
        self.assertEqual(
            result.stdout['name'],
            'Default_Location',
            "Could not find the Default_Location"
        )

    def test_find_admin_user(self):
        """
        @Test: Check if Admin User is present
        @Feature: Smoke Test
        @Assert: Admin User is found and has Admin role
        """

        result = User.info({'login': 'admin'})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code)
        )
        self.assertEqual(
            len(result.stderr),
            0,
            "There was an error fetching the admin user: {0}".format(
                result.stderr)
        )
        self.assertEqual(
            result.stdout['login'],
            'admin',
            "Admin User login does not match: 'admin' != '{0}'".format(
                result.stdout['login'])
        )
        self.assertEqual(
            result.stdout['admin'],
            'yes',
            "Admin User does not have admin role: 'Admin' = '{0}'".format(
                result.stdout['admin'])
        )

    def test_smoke(self):
        """
        @Test: Check that basic content can be created as new user
        @Feature: Smoke Test
        @Assert: All entities are created by new user
        """

        # Create new user
        new_user = make_user({'admin': 'true'})

        # Create new org as new user
        new_org = self._create_entity(
            new_user,
            Org,
            {u'name': self._generate_name()}
        )

        # Create new lifecycle environment 1
        lifecycle1 = self._create_entity(
            new_user,
            LifecycleEnvironment,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name(),
             u'prior': u'Library'}
        )

        # Create new lifecycle environment 2
        lifecycle2 = self._create_entity(
            new_user,
            LifecycleEnvironment,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name(),
             u'prior': lifecycle1['name']}
        )

        # Create a new product
        new_product = self._create_entity(
            new_user,
            Product,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name()}
        )

        # Create a YUM repository
        new_repo1 = self._create_entity(
            new_user,
            Repository,
            {u'product-id': new_product['id'],
             u'name': self._generate_name(),
             u'content-type': u'yum',
             u'publish-via-http': u'true',
             u'url': u'http://dl.google.com/linux/chrome/rpm/stable/x86_64'}
        )

        # Create a Puppet repository
        new_repo2 = self._create_entity(
            new_user,
            Repository,
            {u'product-id': new_product['id'],
             u'name': self._generate_name(),
             u'content-type': u'puppet',
             u'publish-via-http': u'true',
             u'url': u'http://davidd.fedorapeople.org/repos/random_puppet/'}
        )

        # Synchronize YUM repository
        result = Repository.synchronize({'id': new_repo1['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to synchronize YUM repo: {0}".format(result.stderr))

        # Synchronize puppet repository
        result = Repository.synchronize({'id': new_repo2['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to synchronize Puppet repo: {0}".format(result.stderr))

        # Create a Content View
        new_cv = self._create_entity(
            new_user,
            ContentView,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name()}
        )

        # Associate yum repository to content view
        result = ContentView.add_repository(
            {u'id': new_cv['id'],
             u'repository-id': new_repo1['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to add YUM repo to content view: {0}".format(
                result.stderr))

        # Fetch puppet module
        puppet_result = PuppetModule.list(
            {u'repository-id': new_repo2['id'],
             u'per-page': False})
        self.assertEqual(
            puppet_result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(puppet_result.stderr),
            0,
            "Puppet modules list was not generated: {0}".format(result.stderr))

        # Associate puppet repository to content view
        result = ContentView.puppet_module_add(
            {
                u'content-view-id': new_cv['id'],
                u'name': puppet_result.stdout[0]['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to add YUM repo to content view: {0}".format(
                result.stderr))

        # Publish content view
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to publish content view: {0}".format(result.stderr))

        # Only after we publish version1 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Could not fetch content view info: {0}".format(result.stderr))

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Promote content view to first lifecycle
        result = ContentView.version_promote(
            {u'id': result.stdout['versions'][0]['id'],
             u'lifecycle-environment-id': lifecycle1['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to promote content view to lifecycle '{0}': {1}".format(
                lifecycle1['name'], result.stderr))

        # Promote content view to second lifecycle
        result = ContentView.version_promote(
            {u'id': version1_id,
             u'lifecycle-environment-id': lifecycle2['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            "Failed to promote content view to lifecycle '{0}': {1}".format(
                lifecycle2['name'], result.stderr))

    def _generate_name(self):
        """
        Generates a random name string.

        :return: A random string of random length.
        """

        name = unicode(FauxFactory.generate_string(
            FauxFactory.generate_choice(['alpha', 'latin1', 'utf8']),
            FauxFactory.generate_integer(1, 30)))

        return name

    def _create_entity(self, user, entity, attrs):
        """
        Creates a Foreman entity and returns it.

        :param dict user: A python dictionary representing a User
        :param obj entity: A valid CLI entity.
        :param dict attrs: A python dictionary with attributes to use when
            creating entity.
        :return: A python dictionary representing the entity.
        """

        # Create new entity as new user
        result = entity.with_user(
            user['login'],
            user['password']
        ).create(attrs)

        # Assertion
        self.assertEqual(
            len(result.stderr),
            0,
            "Error creating {0}: {1}".format(
                entity.__name__, result.stderr))
        self.assertEqual(
            result.return_code,
            0,
            "Command return code is non-zero: {0}".format(
                result.return_code))

        return result.stdout
