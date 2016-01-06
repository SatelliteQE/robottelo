"""Smoke tests for the ``CLI`` end-to-end scenario."""
import random

from fauxfactory import gen_alphanumeric, gen_ipaddr
from robottelo import manifests, ssh
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
from robottelo.constants import (
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_0_PUPPET_REPO,
    GOOGLE_CHROME_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.config import settings
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import skip_if_not_set
from robottelo.helpers import get_server_software
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine
# (too many public methods) pylint: disable=R0904


class SmokeTestCase(CLITestCase):
    """End-to-end tests using the ``CLI`` path."""

    def test_positive_find_default_org(self):
        """@Test: Check if 'Default Organization' is present

        @Feature: Smoke Test

        @Assert: 'Default Organization' is found

        """
        query = {u'name': DEFAULT_ORG}
        result = self._search(Org, query)
        self.assertEqual(result['name'], DEFAULT_ORG)

    def test_positive_find_default_loc(self):
        """@Test: Check if 'Default Location' is present

        @Feature: Smoke Test

        @Assert: 'Default Location' is found

        """
        query = {u'name': DEFAULT_LOC}
        result = self._search(Location, query)
        self.assertEqual(result['name'], DEFAULT_LOC)

    def test_positive_find_admin_user(self):
        """@Test: Check if Admin User is present

        @Feature: Smoke Test

        @Assert: Admin User is found and has Admin role

        """
        query = {u'login': u'admin'}
        result = self._search(User, query)
        self.assertEqual(result['login'], 'admin')
        self.assertEqual(result['admin'], 'yes')

    def test_positive_foreman_version(self):
        """@Test: Check if /usr/share/foreman/VERSION does not contain the
        develop tag.

        @Feature: Smoke Test

        @Assert: The file content does not have the develop tag.

        """
        result = ssh.command('cat /usr/share/foreman/VERSION')
        self.assertEqual(result.return_code, 0)

        if get_server_software() == 'downstream':
            self.assertNotIn('develop', u''.join(result.stdout))
        else:
            self.assertIn('develop', u''.join(result.stdout))

    def test_positive_smoke(self):
        """@Test: Check that basic content can be created

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
                u'name': gen_alphanumeric(),
                u'organization-id': new_org['id'],
                u'prior': u'Library',
            }
        )

        # Create new lifecycle environment 2
        lifecycle2 = self._create(
            new_user,
            LifecycleEnvironment,
            {
                u'name': gen_alphanumeric(),
                u'organization-id': new_org['id'],
                u'prior': lifecycle1['name'],
            }
        )

        # Create a new product
        new_product = self._create(
            new_user,
            Product,
            {
                u'name': gen_alphanumeric(),
                u'organization-id': new_org['id'],
            }
        )

        # Create a YUM repository
        new_repo1 = self._create(
            new_user,
            Repository,
            {
                u'content-type': u'yum',
                u'name': gen_alphanumeric(),
                u'product-id': new_product['id'],
                u'publish-via-http': u'true',
                u'url': GOOGLE_CHROME_REPO,
            }
        )

        # Create a Puppet repository
        new_repo2 = self._create(
            new_user,
            Repository,
            {
                u'content-type': u'puppet',
                u'name': gen_alphanumeric(),
                u'product-id': new_product['id'],
                u'publish-via-http': u'true',
                u'url': FAKE_0_PUPPET_REPO,
            }
        )

        # Synchronize YUM repository
        Repository.with_user(
            new_user['login'],
            new_user['password']
        ).synchronize({u'id': new_repo1['id']})

        # Synchronize puppet repository
        Repository.with_user(
            new_user['login'],
            new_user['password']
        ).synchronize({u'id': new_repo2['id']})

        # Create a Content View
        new_cv = self._create(
            new_user,
            ContentView,
            {
                u'name': gen_alphanumeric(),
                u'organization-id': new_org['id'],
            }
        )

        # Associate yum repository to content view
        ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo1['id'],
        })

        # Fetch puppet module
        puppet_result = PuppetModule.with_user(
            new_user['login'],
            new_user['password']
        ).list({
            u'repository-id': new_repo2['id'],
            u'per-page': False,
        })

        # Associate puppet repository to content view
        ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).puppet_module_add({
            u'content-view-id': new_cv['id'],
            u'id': puppet_result[0]['id'],
        })

        # Publish content view
        ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).publish({u'id': new_cv['id']})

        # Only after we publish version1 the info is populated.
        result = ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).info({u'id': new_cv['id']})

        # Let us now store the version1 id
        version1_id = result['versions'][0]['id']

        # Promote content view to first lifecycle
        ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': lifecycle1['id'],
        })

        # Promote content view to second lifecycle
        ContentView.with_user(
            new_user['login'],
            new_user['password']
        ).version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': lifecycle2['id'],
        })

        # Create a new libvirt compute resource
        self._create(
            new_user,
            ComputeResource,
            {
                u'name': gen_alphanumeric(),
                u'provider': u'Libvirt',
                u'url': u'qemu+tcp://{0}:16509/system'.format(
                    settings.server.hostname),
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
        # Now look for the puppet environment that matches lifecycle2
        puppet_env = [
            env for env in result
            if env['name'].startswith(env_name)
        ]
        self.assertEqual(len(puppet_env), 1)

        # Create a hostgroup...
        new_hg = self._create(
            new_user,
            HostGroup,
            {
                u'domain-id': new_domain['id'],
                u'environment-id': puppet_env[0]['id'],
                u'name': gen_alphanumeric(),
                u'subnet-id': new_subnet['id'],
            }
        )
        # ...and add it to the organization
        Org.with_user(
            new_user['login'],
            new_user['password']
        ).add_hostgroup({
            u'hostgroup-id': new_hg['id'],
            u'id': new_org['id'],
        })

    def _create(self, user, entity, attrs):
        """Creates a Foreman entity and returns it.

        :param dict user: A python dictionary representing a User
        :param obj entity: A valid CLI entity.
        :param dict attrs: A python dictionary with attributes to use when
            creating entity.
        :return: A ``dict`` representing the Foreman entity.
        :rtype: dict

        """

        # Create new entity as new user
        return entity.with_user(
            user['login'],
            user['password']
        ).create(attrs)

    def _search(self, entity, attrs):
        """Looks up for a Foreman entity by specifying using its ``Info`` CLI
        subcommand with ``attrs`` arguments.

        :param robottelo.cli.Base entity: A logical representation of a
            Foreman CLI entity.
        :param string query: A ``search`` parameter.
        :return: A ``dict`` representing the Foreman entity.
        :rtype: dict

        """

        return entity.info(attrs)

    @skip_if_not_set('clients')
    def test_positive_end_to_end(self):
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
        rhel_product_name = PRDS['rhel']
        rhel_repo_set = REPOSET['rhva6']
        rhel_repo_name = REPOS['rhva6']['name']
        org_name = random.choice(generate_strings_list())
        # Create new org and environment
        new_org = make_org({u'name': org_name})
        new_env = make_lifecycle_environment({
            u'organization-id': new_org['id'],
        })
        # Clone manifest and upload it
        with manifests.clone() as manifest:
            ssh.upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': new_org['id'],
        })
        # Enable repo from Repository Set
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': rhel_repo_set,
            u'organization-id': new_org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
        })
        # Fetch repository info
        rhel_repo = Repository.info({
            u'name': rhel_repo_name,
            u'organization-id': new_org['id'],
            u'product': rhel_product_name,
        })
        # Synchronize the repository
        Repository.synchronize({
            u'name': rhel_repo_name,
            u'organization-id': new_org['id'],
            u'product': rhel_product_name,
        })
        # Create CV and associate repo to it
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': new_org['id'],
            u'repository-id': rhel_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Get the CV info
        version1_id = ContentView.info({
            u'id': new_cv['id']})['versions'][0]['id']
        # Store the version1 id
        # Promotion of version1 to next env
        ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': new_env['id'],
        })
        # Create activation key
        activation_key = make_activation_key({
            u'content-view': new_cv['name'],
            u'lifecycle-environment-id': new_env['id'],
            u'organization-id': new_org['id'],
        })
        # List the subscriptions in given org
        result = Subscription.list(
            {u'organization-id': new_org['id']},
            per_page=False
        )
        self.assertGreater(len(result), 0)
        # Get the subscription ID from subscriptions list
        subscription_quantity = 0
        for subscription in result:
            if subscription['name'] == DEFAULT_SUBSCRIPTION_NAME:
                subscription_id = subscription['id']
                subscription_quantity = int(subscription['quantity'])
        self.assertGreater(subscription_quantity, 0)
        # Add the subscriptions to activation-key
        ActivationKey.add_subscription({
            u'id': activation_key['id'],
            u'quantity': 1,
            u'subscription-id': subscription_id,
        })
        # Enable product content
        ActivationKey.content_override({
            u'content-label': 'rhel-6-server-rhev-agent-rpms',
            u'id': activation_key['id'],
            u'organization-id': new_org['id'],
            u'value': '1',
        })
        # Create VM
        package_name = "python-kitchen"
        server_name = settings.server.hostname
        with VirtualMachine(distro='rhel66') as vm:
            # Download and Install rpm
            result = vm.run(
                "wget -nd -r -l1 --no-parent -A '*.noarch.rpm' http://{0}/pub/"
                .format(server_name)
            )
            self.assertEqual(result.return_code, 0)
            result = vm.run(
                'rpm -i katello-ca-consumer*.noarch.rpm'
            )
            self.assertEqual(result.return_code, 0)
            # Register client with foreman server using activation-key
            result = vm.run(
                u'subscription-manager register --activationkey {0} '
                '--org {1} --force'
                .format(activation_key['name'], new_org['label'])
            )
            self.assertEqual(result.return_code, 0)
            # Install contents from sat6 server
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)
            # Verify if package is installed by query it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)
