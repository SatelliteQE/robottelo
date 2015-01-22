"""Smoke tests for the ``CLI`` end-to-end scenario."""
from ddt import ddt
from fauxfactory import gen_alphanumeric, gen_ipaddr
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contentview import ContentView
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    make_user, make_org, make_lifecycle_environment, make_content_view,
    make_activation_key)
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.repository import Repository
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.common.constants import FAKE_0_PUPPET_REPO, GOOGLE_CHROME_REPO
from robottelo.common.helpers import generate_strings_list
from robottelo.common import manifests
from robottelo.common.ssh import upload_file
from robottelo.common import conf
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine
import random
# (too many public methods) pylint: disable=R0904


@ddt
class TestSmoke(CLITestCase):
    """End-to-end tests using the ``CLI`` path."""

    def test_find_default_org(self):
        """
        @Test: Check if 'Default Organization' is present
        @Feature: Smoke Test
        @Assert: 'Default Organization' is found
        """

        query = {u'name': u'Default_Organization'}
        result = self._search(Org, query)
        self.assertEqual(
            result.stdout['name'],
            'Default_Organization',
            u"Could not find the Default Organization"
        )

    def test_find_default_location(self):
        """
        @Test: Check if 'Default Location' is present
        @Feature: Smoke Test
        @Assert: 'Default Location' is found
        """

        query = {u'name': u'Default_Location'}
        result = self._search(Location, query)
        self.assertEqual(
            result.stdout['name'],
            'Default_Location',
            u"Could not find the 'Default Location'"
        )

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
            * Create a new hostgroup and associate previous entities to it

        @Feature: Smoke Test
        @Assert: All entities are created and associated.
        """

        # Create new user
        password = gen_alphanumeric()
        new_user = make_user({u'admin': u'true', u'password': password})

        # Append the password as the info command does not return it
        new_user[u'password'] = password

        # Create new org as new user
        new_org = self._create(
            new_user,
            Org,
            {u'name': gen_alphanumeric()}
        )

        # Create new lifecycle environment 1
        lifecycle1 = self._create(
            new_user,
            LifecycleEnvironment,
            {
                u'organization-id': new_org['id'],
                u'name': gen_alphanumeric(),
                u'prior': u'Library',
            }
        )

        # Create new lifecycle environment 2
        lifecycle2 = self._create(
            new_user,
            LifecycleEnvironment,
            {
                u'organization-id': new_org['id'],
                u'name': gen_alphanumeric(),
                u'prior': lifecycle1['name'],
            }
        )

        # Create a new product
        new_product = self._create(
            new_user,
            Product,
            {
                u'organization-id': new_org['id'],
                u'name': gen_alphanumeric(),
            }
        )

        # Create a YUM repository
        new_repo1 = self._create(
            new_user,
            Repository,
            {
                u'product-id': new_product['id'],
                u'name': gen_alphanumeric(),
                u'content-type': u'yum',
                u'publish-via-http': u'true',
                u'url': GOOGLE_CHROME_REPO,
            }
        )

        # Create a Puppet repository
        new_repo2 = self._create(
            new_user,
            Repository,
            {
                u'product-id': new_product['id'],
                u'name': gen_alphanumeric(),
                u'content-type': u'puppet',
                u'publish-via-http': u'true',
                u'url': FAKE_0_PUPPET_REPO,
            }
        )

        # Synchronize YUM repository
        result = Repository.with_user(
            new_user['login'],
            new_user['password']
        ).synchronize({u'id': new_repo1['id']})
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
        ).synchronize({u'id': new_repo2['id']})
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
            {
                u'organization-id': new_org['id'],
                u'name': gen_alphanumeric(),
            }
        )

        # Associate yum repository to content view
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo1['id'],
        })
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
        ).list({
            u'repository-id': new_repo2['id'],
            u'per-page': False,
        })
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
        ).puppet_module_add({
            u'content-view-id': new_cv['id'],
            u'id': puppet_result.stdout[0]['id'],
        })
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
        ).version_promote({
            u'id': result.stdout['versions'][0]['id'],
            u'to-lifecycle-environment-id': lifecycle1['id'],
        })
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
        ).version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': lifecycle2['id'],
        })
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
                u'name': gen_alphanumeric(),
                u'provider': u'Libvirt',
                u'url': u'qemu+tcp://{0}:16509/system'.format(
                    conf.properties['main.server.hostname']),
            }
        )

        # Create a new subnet
        new_subnet = self._create(
            new_user,
            Subnet,
            {
                u'name': gen_alphanumeric(),
                u'network': gen_ipaddr(ip3=True),
                u'mask': u'255.255.255.0',
            }
        )

        # Create a domain
        new_domain = self._create(
            new_user,
            Domain,
            {
                u'name': gen_alphanumeric(),
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
        ).list({
            u'search': u'organization="{0}"'.format(new_org['name']),
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

        # Create a hostgroup...
        new_hg = self._create(
            new_user,
            HostGroup,
            {
                u'name': gen_alphanumeric(),
                u'domain-id': new_domain['id'],
                u'subnet-id': new_subnet['id'],
                u'environment-id': puppet_env[0]['id'],
            }
        )
        # ...and add it to the organization
        result = Org.with_user(
            new_user['login'],
            new_user['password']
        ).add_hostgroup({
            u'id': new_org['id'],
            u'hostgroup-id': new_hg['id'],
        })
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

    def test_end_to_end(self):
        """@Test: Perform end to end smoke tests using RH repos.

        1. Create new organization and environment
        2. Upload manifest
        3. Sync a RedHat repository
        4. Create content-view
        5. Add repository to contet-view
        6. Promote/publish content-view
        7. Create an activation-key
        8. Add product to activation-key
        9. Create new virtualmachine
        10. Pull rpm from Foreman server and install on client
        11. Register client with foreman server using activation-key
        12. Install rpm on client

        @Feature: Smoke test

        @Assert: All tests should succeed and Content should be successfully
        fetched by client

        """
        # Product, RepoSet and repository variables
        rhel_product_name = 'Red Hat Enterprise Linux Server'
        rhel_repo_set = (
            'Red Hat Enterprise Virtualization Agents '
            'for RHEL 6 Server (RPMs)'
        )
        rhel_repo_name = (
            'Red Hat Enterprise Virtualization Agents '
            'for RHEL 6 Server '
            'RPMs x86_64 6Server'
        )
        org_name = random.choice(generate_strings_list())
        # Create new org and environment
        new_org = make_org({u'name': org_name})
        new_env = make_lifecycle_environment({
            u'organization-id': new_org['id'],
            u'name': gen_alphanumeric(),
        })
        # Clone manifest and upload it
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': new_org['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Failed to upload manifest: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Enable repo from Repository Set
        result = RepositorySet.enable({
            u'name': rhel_repo_set,
            u'organization-id': new_org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(
            result.return_code, 0,
            "Repo was not enabled: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Fetch repository info
        result = Repository.info({
            u'name': rhel_repo_name,
            u'product': rhel_product_name,
            u'organization-id': new_org['id'],
        })
        rhel_repo = result.stdout
        # Synchronize the repository
        result = Repository.synchronize({
            u'name': rhel_repo_name,
            u'organization-id': new_org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            result.return_code, 0,
            "Repo was not synchronized: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Create CV and associate repo to it
        new_cv = make_content_view({u'organization-id': new_org['id']})
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': rhel_repo['id'],
            u'organization-id': new_org['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Failed repository association: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Version1 publishing failed: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Get the CV info
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "ContentView was not found: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Store the version1 id
        version1_id = result.stdout['versions'][0]['id']
        # Promotion of version1 to next env
        result = ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': new_env['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "version1 promotion failed: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Create activation key
        activation_key = make_activation_key({
            u'name': gen_alphanumeric(),
            u'lifecycle-environment-id': new_env['id'],
            u'organization-id': new_org['id'],
            u'content-view': new_cv['name'],
        })
        # List the subscriptions in given org
        result = Subscription.list(
            {u'organization-id': new_org['id']},
            per_page=False
        )
        self.assertEqual(
            result.return_code, 0,
            "Failed to list subscriptions: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Get the subscription ID from subscriptions list
        for subscription in result.stdout:
            if subscription['name'] == "Red Hat Employee Subscription":
                subscription_id = subscription['id']
                subscription_quantity = int(subscription['quantity'])
        self.assertGreater(
            int(subscription_quantity), 0,
            'Unexpected subscription quantity {0}'
            .format(subscription_quantity)
        )
        # Add the subscriptions to activation-key
        result = ActivationKey.add_subscription({
            u'id': activation_key['id'],
            u'subscription-id': subscription_id,
            u'quantity': 1,
        })
        self.assertEqual(
            result.return_code, 0,
            "Failed to add subscription: {0} and return code: {1}"
            .format(result.stderr, result.return_code)
        )
        # Create VM
        package_name = "python-kitchen"
        server_name = conf.properties['main.server.hostname']
        with VirtualMachine(distro='rhel65') as vm:
            # Download and Install rpm
            result = vm.run(
                "wget -nd -r -l1 --no-parent -A '*.noarch.rpm' http://{0}/pub/"
                .format(server_name)
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to fetch katello-ca rpm: {0}, return code: {1}"
                .format(result.stderr, result.return_code)
            )
            result = vm.run(
                'rpm -i katello-ca-consumer*.noarch.rpm'
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to install katello-ca rpm: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Register client with foreman server using activation-key
            result = vm.run(
                u'subscription-manager register --activationkey {0} '
                '--org {1} --force'
                .format(activation_key['name'], new_org['label'])
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to register client:: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Install contents from sat6 server
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(
                result.return_code, 0,
                "Package install failed: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Verify if package is installed by query it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertIn(package_name, result.stdout[0])
