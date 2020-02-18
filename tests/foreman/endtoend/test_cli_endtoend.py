# coding=utf-8
"""Smoke tests for the ``CLI`` end-to-end scenario.

:Requirement: Cli Endtoend

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hammer

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from fauxfactory import gen_alphanumeric
from fauxfactory import gen_ipaddr

from .utils import AK_CONTENT_LABEL
from .utils import ClientProvisioningMixin
from robottelo import manifests
from robottelo import ssh
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contentview import ContentView
from robottelo.cli.domain import Domain
from robottelo.cli.factory import make_user
from robottelo.cli.host import Host
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import CUSTOM_RPM_REPO
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import FAKE_0_PUPPET_REPO
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import setting_is_set
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier4
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class EndToEndTestCase(CLITestCase, ClientProvisioningMixin):
    """End-to-end tests using the ``CLI`` path."""

    @classmethod
    def setUpClass(cls):  # noqa
        super(EndToEndTestCase, cls).setUpClass()
        cls.fake_manifest_is_set = setting_is_set('fake_manifest')

    @tier1
    @upgrade
    def test_positive_find_default_org(self):
        """Check if 'Default Organization' is present

        :id: 95ffeb7a-134e-4273-bccc-fe8a3a336b2a

        :expectedresults: 'Default Organization' is found
        """
        result = Org.info({u'name': DEFAULT_ORG})
        self.assertEqual(result['name'], DEFAULT_ORG)

    @tier1
    @upgrade
    def test_positive_find_default_loc(self):
        """Check if 'Default Location' is present

        :id: 11cf0d06-78ff-47e8-9d50-407a2ea31988

        :expectedresults: 'Default Location' is found
        """
        result = Location.info({u'name': DEFAULT_LOC})
        self.assertEqual(result['name'], DEFAULT_LOC)

    @tier1
    @upgrade
    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        :id: f6755189-05a6-4d2f-a3b8-98be0cfacaee

        :expectedresults: Admin User is found and has Admin role
        """
        result = User.info({u'login': u'admin'})
        self.assertEqual(result['login'], 'admin')
        self.assertEqual(result['admin'], 'yes')

    @skip_if_not_set('compute_resources')
    @tier4
    @upgrade
    def test_positive_end_to_end(self):
        """Perform end to end smoke tests using RH and custom repos.

        1. Create a new user with admin permissions
        2. Using the new user from above
            1. Create a new organization
            2. Clone and upload manifest
            3. Create a new lifecycle environment
            4. Create a custom product
            5. Create a custom YUM repository
            6. Create a custom PUPPET repository
            7. Enable a Red Hat repository
            8. Synchronize the three repositories
            9. Create a new content view
            10. Associate the YUM and Red Hat repositories to new content view
            11. Add a PUPPET module to new content view
            12. Publish content view
            13. Promote content view to the lifecycle environment
            14. Create a new activation key
            15. Add the products to the activation key
            16. Create a new libvirt compute resource
            17. Create a new subnet
            18. Create a new domain
            19. Create a new hostgroup and associate previous entities to it
            20. Provision a client

        :id: 8c8b3ffa-0d54-436b-8eeb-1a3542e100a8

        :expectedresults: All tests should succeed and Content should be
            successfully fetched by client.
        """
        # step 1: Create a new user with admin permissions
        password = gen_alphanumeric()
        user = make_user({u'admin': u'true', u'password': password})
        user['password'] = password

        # step 2.1: Create a new organization
        org = self._create(user, Org, {u'name': gen_alphanumeric()})

        # step 2.2: Clone and upload manifest
        if self.fake_manifest_is_set:
            with manifests.clone() as manifest:
                ssh.upload_file(manifest.content, manifest.filename)
            Subscription.upload({u'file': manifest.filename, u'organization-id': org['id']})

        # step 2.3: Create a new lifecycle environment
        lifecycle_environment = self._create(
            user,
            LifecycleEnvironment,
            {u'name': gen_alphanumeric(), u'organization-id': org['id'], u'prior': u'Library'},
        )

        # step 2.4: Create a custom product
        product = self._create(
            user, Product, {u'name': gen_alphanumeric(), u'organization-id': org['id']}
        )
        repositories = []

        # step 2.5: Create custom YUM repository
        yum_repo = self._create(
            user,
            Repository,
            {
                u'content-type': u'yum',
                u'name': gen_alphanumeric(),
                u'product-id': product['id'],
                u'publish-via-http': u'true',
                u'url': CUSTOM_RPM_REPO,
            },
        )
        repositories.append(yum_repo)

        # step 2.6: Create custom PUPPET repository
        puppet_repo = self._create(
            user,
            Repository,
            {
                u'content-type': u'puppet',
                u'name': gen_alphanumeric(),
                u'product-id': product['id'],
                u'publish-via-http': u'true',
                u'url': FAKE_0_PUPPET_REPO,
            },
        )
        repositories.append(puppet_repo)

        # step 2.7: Enable a Red Hat repository
        if self.fake_manifest_is_set:
            RepositorySet.enable(
                {
                    u'basearch': 'x86_64',
                    u'name': REPOSET['rhva6'],
                    u'organization-id': org['id'],
                    u'product': PRDS['rhel'],
                    u'releasever': '6Server',
                }
            )
            rhel_repo = Repository.info(
                {
                    u'name': REPOS['rhva6']['name'],
                    u'organization-id': org['id'],
                    u'product': PRDS['rhel'],
                }
            )
            repositories.append(rhel_repo)

        # step 2.8: Synchronize the three repositories
        for repo in repositories:
            Repository.with_user(user['login'], user['password']).synchronize({u'id': repo['id']})

        # step 2.9: Create content view
        content_view = self._create(
            user, ContentView, {u'name': gen_alphanumeric(), u'organization-id': org['id']}
        )

        # step 2.10: Associate the YUM and Red Hat repositories to new content
        # view
        repositories.remove(puppet_repo)
        for repo in repositories:
            ContentView.add_repository(
                {
                    u'id': content_view['id'],
                    u'organization-id': org['id'],
                    u'repository-id': repo['id'],
                }
            )

        # step 2.11: Add a PUPPET module to new content view
        result = PuppetModule.with_user(user['login'], user['password']).list(
            {u'repository-id': puppet_repo['id'], u'per-page': False}
        )
        ContentView.with_user(user['login'], user['password']).puppet_module_add(
            {u'content-view-id': content_view['id'], u'id': random.choice(result)['id']}
        )

        # step 2.12: Publish content view
        ContentView.with_user(user['login'], user['password']).publish({u'id': content_view['id']})

        # step 2.13: Promote content view to the lifecycle environment
        content_view = ContentView.with_user(user['login'], user['password']).info(
            {u'id': content_view['id']}
        )
        self.assertEqual(len(content_view['versions']), 1)
        cv_version = ContentView.with_user(user['login'], user['password']).version_info(
            {'id': content_view['versions'][0]['id']}
        )
        self.assertEqual(len(cv_version['lifecycle-environments']), 1)
        ContentView.with_user(user['login'], user['password']).version_promote(
            {u'id': cv_version['id'], u'to-lifecycle-environment-id': lifecycle_environment['id']}
        )
        # check that content view exists in lifecycle
        content_view = ContentView.with_user(user['login'], user['password']).info(
            {u'id': content_view['id']}
        )
        self.assertEqual(len(content_view['versions']), 1)
        cv_version = ContentView.with_user(user['login'], user['password']).version_info(
            {'id': content_view['versions'][0]['id']}
        )
        self.assertEqual(len(cv_version['lifecycle-environments']), 2)
        self.assertEqual(
            cv_version['lifecycle-environments'][-1]['id'], lifecycle_environment['id']
        )

        # step 2.14: Create a new activation key
        activation_key = self._create(
            user,
            ActivationKey,
            {
                u'content-view-id': content_view['id'],
                u'lifecycle-environment-id': lifecycle_environment['id'],
                u'name': gen_alphanumeric(),
                u'organization-id': org['id'],
            },
        )

        # step 2.15: Add the products to the activation key
        subscription_list = Subscription.with_user(user['login'], user['password']).list(
            {u'organization-id': org['id']}, per_page=False
        )
        for subscription in subscription_list:
            if subscription['name'] == DEFAULT_SUBSCRIPTION_NAME:
                ActivationKey.with_user(user['login'], user['password']).add_subscription(
                    {
                        u'id': activation_key['id'],
                        u'quantity': 1,
                        u'subscription-id': subscription['id'],
                    }
                )

        # step 2.15.1: Enable product content
        if self.fake_manifest_is_set:
            ActivationKey.with_user(user['login'], user['password']).content_override(
                {
                    u'content-label': AK_CONTENT_LABEL,
                    u'id': activation_key['id'],
                    u'organization-id': org['id'],
                    u'value': '1',
                }
            )

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host_name = gen_alphanumeric()
        content_host = Host.with_user(user['login'], user['password']).subscription_register(
            {
                u'content-view-id': content_view['id'],
                u'lifecycle-environment-id': lifecycle_environment['id'],
                u'name': content_host_name,
                u'organization-id': org['id'],
            }
        )

        content_host = Host.with_user(user['login'], user['password']).info(
            {'id': content_host['id']}
        )
        # check that content view matches what we passed
        self.assertEqual(
            content_host['content-information']['content-view']['name'], content_view['name']
        )
        # check that lifecycle environment matches
        self.assertEqual(
            content_host['content-information']['lifecycle-environment']['name'],
            lifecycle_environment['name'],
        )

        # step 2.16: Create a new libvirt compute resource
        self._create(
            user,
            ComputeResource,
            {
                u'name': gen_alphanumeric(),
                u'provider': u'Libvirt',
                u'url': u'qemu+ssh://root@{0}/system'.format(
                    settings.compute_resources.libvirt_hostname
                ),
            },
        )

        # step 2.17: Create a new subnet
        subnet = self._create(
            user,
            Subnet,
            {
                u'name': gen_alphanumeric(),
                u'network': gen_ipaddr(ip3=True),
                u'mask': u'255.255.255.0',
            },
        )

        # step 2.18: Create a new domain
        domain = self._create(user, Domain, {u'name': gen_alphanumeric()})

        # step 2.19: Create a new hostgroup and associate previous entities to
        # it
        host_group = self._create(
            user,
            HostGroup,
            {u'domain-id': domain['id'], u'name': gen_alphanumeric(), u'subnet-id': subnet['id']},
        )
        HostGroup.with_user(user['login'], user['password']).update(
            {
                'id': host_group['id'],
                'organization-ids': org['id'],
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': lifecycle_environment['id'],
            }
        )

        # step 2.20: Provision a client
        self.client_provisioning(activation_key['name'], org['label'])

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
        return entity.with_user(user['login'], user['password']).create(attrs)
