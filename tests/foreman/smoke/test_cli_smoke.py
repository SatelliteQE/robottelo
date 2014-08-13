"""Smoke tests for the ``CLI`` end-to-end scenario."""
from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contentview import ContentView
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_user
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.subnet import Subnet
from robottelo.cli.user import User
from robottelo.common import conf
from robottelo.test import CLITestCase
# (too many public methods) pylint: disable=R0904


@ddt
class TestSmoke(CLITestCase):
    """End-to-end tests using the ``CLI`` path."""

    @attr('smoke')
    def test_find_default_org(self):
        """
        @Test: Check if 'Default Organization' is present
        @Feature: Smoke Test
        @Assert: 'Default Organization' is found
        """

        query = {u'name': u'Default Organization'}
        result = self._search(Org, query)
        self.assertEqual(
            result.stdout['name'],
            'Default Organization',
            u"Could not find the Default Organization"
        )

    @attr('smoke')
    def test_find_default_location(self):
        """
        @Test: Check if 'Default Location' is present
        @Feature: Smoke Test
        @Assert: 'Default Location' is found
        """

        query = {u'name': u'Default Location'}
        result = self._search(Location, query)
        self.assertEqual(
            result.stdout['name'],
            'Default Location',
            u"Could not find the 'Default Location'"
        )

    @attr('smoke')
    def test_find_admin_user(self):
        """
        @Test: Check if Admin User is present
        @Feature: Smoke Test
        @Assert: Admin User is found and has Admin role
        """

        query = {u'login': u'admin'}
        result = self._search(User, query)
        self.assertEqual(
            result.stdout['login'],
            'admin',
            u"Admin User login does not match: 'admin' != '{0}'".format(
                result.stdout['login'])
        )
        self.assertEqual(
            result.stdout['admin'],
            'yes',
            u"Admin User does not have admin role: 'Admin' = '{0}'".format(
                result.stdout['admin'])
        )

    @attr('smoke')
    def test_smoke(self):
        """
        @Test: Check that basic content can be created
        * Create a new user with admin permissions
        * Using the new user from above:

            * Create a new organization
            * Create two new lifecycle environments
            * Create a custom product
            * Create a custom YUM repository
            * Create a custom PUPPET repository
            * Synchronize both custom repositories
            * Create a new content view
            * Associate both repositories to new content view
            * Publish content view
            * Promote content view to both lifecycles
            * Create a new libvirt compute resource
            * Create a new subnet
            * Create a new domain
            * Create a new capsule
            * Create a new hostgroup and associate previous entities to it

        @Feature: Smoke Test
        @Assert: All entities are created and associated.
        """

        # Create new user
        new_user = make_user({'admin': 'true'})

        # Create new org as new user
        new_org = self._create(
            new_user,
            Org,
            {u'name': self._generate_name()}
        )

        # Create new lifecycle environment 1
        lifecycle1 = self._create(
            new_user,
            LifecycleEnvironment,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name(),
             u'prior': u'Library'}
        )

        # Create new lifecycle environment 2
        lifecycle2 = self._create(
            new_user,
            LifecycleEnvironment,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name(),
             u'prior': lifecycle1['name']}
        )

        # Create a new product
        new_product = self._create(
            new_user,
            Product,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name()}
        )

        # Create a YUM repository
        new_repo1 = self._create(
            new_user,
            Repository,
            {u'product-id': new_product['id'],
             u'name': self._generate_name(),
             u'content-type': u'yum',
             u'publish-via-http': u'true',
             u'url': u'http://dl.google.com/linux/chrome/rpm/stable/x86_64'}
        )

        # Create a Puppet repository
        new_repo2 = self._create(
            new_user,
            Repository,
            {u'product-id': new_product['id'],
             u'name': self._generate_name(),
             u'content-type': u'puppet',
             u'publish-via-http': u'true',
             u'url': u'http://davidd.fedorapeople.org/repos/random_puppet/'}
        )

        # Synchronize YUM repository
        result = Repository.with_user(
            new_user['login'],
            new_user['password']
        ).synchronize({'id': new_repo1['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to synchronize YUM repo: {0}".format(result.stderr))

        # Synchronize puppet repository
        result = Repository.with_user(
            new_user['login'],
            new_user['password']
        ).synchronize({'id': new_repo2['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to synchronize Puppet repo: {0}".format(result.stderr))

        # Create a Content View
        new_cv = self._create(
            new_user,
            ContentView,
            {u'organization-id': new_org['id'],
             u'name': self._generate_name()}
        )

        # Associate yum repository to content view
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).add_repository(
            {u'id': new_cv['id'],
             u'repository-id': new_repo1['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to add YUM repo to content view: {0}".format(
                result.stderr))

        # Fetch puppet module
        puppet_result = PuppetModule.with_user(
            new_user['login'],
            new_user['password']
        ).list(
            {u'repository-id': new_repo2['id'],
             u'per-page': False})
        self.assertEqual(
            puppet_result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(puppet_result.stderr),
            0,
            u"Puppet modules list was not generated: {0}".format(
                result.stderr))

        # Associate puppet repository to content view
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).puppet_module_add(
            {
                u'content-view-id': new_cv['id'],
                u'name': puppet_result.stdout[0]['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to add YUM repo to content view: {0}".format(
                result.stderr))

        # Publish content view
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to publish content view: {0}".format(result.stderr))

        # Only after we publish version1 the info is populated.
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Could not fetch content view info: {0}".format(result.stderr))

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Promote content view to first lifecycle
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).version_promote(
            {u'id': result.stdout['versions'][0]['id'],
             u'lifecycle-environment-id': lifecycle1['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to promote content view to lifecycle '{0}': {1}".format(
                lifecycle1['name'], result.stderr))

        # Promote content view to second lifecycle
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).version_promote(
            {u'id': version1_id,
             u'lifecycle-environment-id': lifecycle2['id']})
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to promote content view to lifecycle '{0}': {1}".format(
                lifecycle2['name'], result.stderr))

        # Create a new libvirt compute resource
        result = self._create(
            new_user,
            ComputeResource,
            {
                u'name': self._generate_name(),
                u'provider': u'Libvirt',
                u'url': u'qemu+tcp://{0}:16509/system'.format(
                    conf.properties['main.server.hostname'])
            })

        # Create a new subnet
        new_subnet = self._create(
            new_user,
            Subnet,
            {
                u'name': self._generate_name(),
                u'network': FauxFactory.generate_ipaddr(ip3=True),
                u'mask': u'255.255.255.0'
            }
        )

        # Create a domain
        new_domain = self._create(
            new_user,
            Domain,
            {
                u'name': self._generate_name(),
            }
        )

        # Fetch Puppet environment for second lifecycle
        # (unfortunately it is not straight forward to extract this)

        # The puppet environment we want has a name like this...
        env_name = u'KT_{0}_{1}_'.format(
            #  Hyphens are replaced by underscores
            new_org['label'].replace('-', '_',),
            lifecycle2['label'].replace('-', '_')
        )
        # We fetch all the puppet environments for our organization...
        result = Environment.with_user(
            new_user['login'],
            new_user['password']
        ).list(
            {
                u'search': u'organization=\"{0}\"'.format(
                    new_org['name'])
            })
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to fetch puppet environments: {0}".format(
                result.stderr))
        # Now look for the puppet environment that matches lifecycle2
        puppet_env = [
            env for env in result.stdout if env['name'].startswith(
                env_name)]
        self.assertEqual(
            len(puppet_env),
            1,
            u'Could not find the puppet environment: {0}'.format(env_name))

        # Create new Capsule...
        new_capsule = self._create(
            new_user,
            Proxy,
            {
                u'name': self._generate_name(),
                u'url': u'https://{0}:9090/'.format(
                    conf.properties['main.server.hostname'])
            }
        )
        # ...and add it to the organization
        result = Org.with_user(
            new_user['login'],
            new_user['password']
        ).add_smart_proxy(
            {
                u'id': new_org['id'],
                u'smart-proxy-id': new_capsule['id']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to add capsule '{0}' to org '{1}': {2}".format(
                new_capsule['name'], new_org['name'], result.stderr))

        # Create a hostgroup...
        new_hg = self._create(
            new_user,
            HostGroup,
            {
                u'name': self._generate_name(),
                u'domain-id': new_domain['id'],
                u'subnet-id': new_subnet['id'],
                u'environment-id': puppet_env[0]['id'],
                u'puppet-ca-proxy-id': new_capsule['id'],
                u'puppet-proxy-id': new_capsule['id'],
            }
        )
        # ...and add it to the organization
        result = Org.with_user(
            new_user['login'],
            new_user['password']
        ).add_hostgroup(
            {
                u'id': new_org['id'],
                u'hostgroup-id': new_hg['id']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code))
        self.assertEqual(
            len(result.stderr),
            0,
            u"Failed to add hostgroup '{0}' to org '{1}': {2}".format(
                new_hg['name'], new_org['name'], result.stderr))

    def _create(self, user, entity, attrs):
        """
        Creates a Foreman entity and returns it.

        :param dict user: A python dictionary representing a User
        :param obj entity: A valid CLI entity.
        :param dict attrs: A python dictionary with attributes to use when
            creating entity.
        :return: A ``dict`` representing the Foreman entity.
        :rtype: dict
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

    def _generate_name(self):
        """
        Generates a random name string.

        :return: A random string of random length.
        :rtype: str
        """

        name = unicode(FauxFactory.generate_string(
            FauxFactory.generate_choice(['alpha', 'cjk', 'latin1', 'utf8']),
            FauxFactory.generate_integer(1, 30)))

        return name

    def _search(self, entity, attrs):
        """
        Looks up for a Foreman entity by specifying using its ``Info``
        CLI subcommand with ``attrs`` arguments.

        :param robottelo.cli.Base entity: A logical representation of a
            Foreman CLI entity.
        :param string query: A ``search`` parameter.
        :return: A ``SSHCommandResult`` instance.
        :rtype: robottelo.common.ssh.SSHCommandResult
        """
        result = entity.info(attrs)
        self.assertEqual(
            result.return_code,
            0,
            u"Return code is non-zero: {0}".format(result.return_code)
        )
        self.assertEqual(
            len(result.stderr),
            0,
            u"There was an error fetching the entity: {0}".format(
                result.stderr)
        )

        return result
