# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for Content-Host CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_host,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.common import conf
from robottelo.common import manifests
from robottelo.common.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_ERRATA_ID,
    FAKE_0_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.ssh import upload_file
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


@ddt
class TestContentHost(CLITestCase):
    """content-host CLI tests."""

    NEW_ORG = None
    NEW_CV = None
    PROMOTED_CV = None
    NEW_LIFECYCLE = None
    LIBRARY = None
    DEFAULT_CV = None

    def setUp(self):  # noqa
        """Tests for Content Host via Hammer CLI"""

        super(TestContentHost, self).setUp()

        if TestContentHost.NEW_ORG is None:
            TestContentHost.NEW_ORG = make_org(cached=True)
        if TestContentHost.NEW_LIFECYCLE is None:
            TestContentHost.NEW_LIFECYCLE = make_lifecycle_environment(
                {u'organization-id': TestContentHost.NEW_ORG['id']},
                cached=True)
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
        if TestContentHost.NEW_CV is None:
            TestContentHost.NEW_CV = make_content_view(
                {u'organization-id': TestContentHost.NEW_ORG['id']}
            )
            TestContentHost.PROMOTED_CV = None
            cv_id = TestContentHost.NEW_CV['id']
            ContentView.publish({u'id': cv_id})
            result = ContentView.version_list({u'content-view-id': cv_id})
            version_id = result.stdout[0]['id']
            promotion = ContentView.version_promote({
                u'id': version_id,
                u'to-lifecycle-environment-id': TestContentHost.NEW_LIFECYCLE[
                    'id'],
                u'organization-id': TestContentHost.NEW_ORG['id']
            })
            if promotion.stderr == []:
                TestContentHost.PROMOTED_CV = TestContentHost.NEW_CV

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_1(self, test_data):
        """@Test: Check if content host can be created with random names

        @Feature: Content Hosts

        @Assert: Content host is created and has random name

        """

        new_system = make_content_host({
            u'name': test_data['name'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
        })
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {u'description': gen_string('alpha', 15)},
        {u'description': gen_string('alphanumeric', 15)},
        {u'description': gen_string('numeric', 15)},
        {u'description': gen_string('latin1', 15)},
        {u'description': gen_string('utf8', 15)},
        {u'description': gen_string('html', 15)},
    )
    def test_positive_create_2(self, test_data):
        """@Test: Check if content host can be created with random description

        @Feature: Content Hosts

        @Assert: Content host is created and has random description

        """

        new_system = make_content_host({
            u'description': test_data['description'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
        })
        # Assert that description matches data passed
        self.assertEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    def test_positive_create_3(self):
        """@Test: Check if content host can be created with organization name

        @Feature: Content Hosts

        @Assert: Content host is created using organization name

        """

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization': self.NEW_ORG['name'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
        })
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

    def test_positive_create_4(self):
        """@Test: Check if content host can be created with organization label

        @Feature: Content Hosts

        @Assert: Content host is created using organization label

        """

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization-label': self.NEW_ORG['label'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
        })
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

    @run_only_on('sat')
    def test_positive_create_5(self):
        """@Test: Check if content host can be created with content view name

        @Feature: Content Hosts

        @Assert: Content host is created using content view name

        """

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view': self.DEFAULT_CV['name'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
        })
        # Assert that name matches data passed
        self.assertEqual(
            new_system['content-view'],
            self.DEFAULT_CV['name'],
            "Content views don't match"
        )

    @run_only_on('sat')
    def test_positive_create_6(self):
        """@Test: Check if content host can be created with lifecycle name

        @Feature: Content Hosts

        @Assert: Content host is created using lifecycle name

        """

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment': self.LIBRARY['name']})
        # Assert that lifecycles matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
            "Lifecycle environments don't match"
        )

    @run_only_on('sat')
    def test_positive_create_7(self):
        """@Test: Check if content host can be created with new lifecycle

        @Feature: Content Hosts

        @Assert: Content host is created using new lifecycle

        """

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.PROMOTED_CV['id'],
            u'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
        })
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.NEW_LIFECYCLE['name'],
            "Environments don't match"
        )

    @run_only_on('sat')
    def test_positive_create_8(self):
        """@Test: Check if content host can be created with new content view

        @Feature: Content Hosts

        @Assert: Content host is created using new published, promoted cv

        """

        if TestContentHost.PROMOTED_CV is None:
            self.fail("Couldn't prepare promoted contentview for this test")

        new_system = make_content_host({
            u'name': gen_string('alpha', 15),
            u'organization-id': TestContentHost.NEW_ORG['id'],
            u'content-view-id': TestContentHost.PROMOTED_CV['id'],
            u'lifecycle-environment-id': TestContentHost.NEW_LIFECYCLE['id'],
        })
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['content-view'],
            TestContentHost.PROMOTED_CV['name'],
            "Content Views don't match"
        )

    @data(
        {u'name': gen_string('alpha', 300)},
        {u'name': gen_string('alphanumeric', 300)},
        {u'name': gen_string('numeric', 300)},
        {u'name': gen_string('latin1', 300)},
        {u'name': gen_string('utf8', 300)},
        {u'name': gen_string('html', 300)},
    )
    def test_negative_create_1(self, test_data):
        """@Test: Check if content host can be created with random long names

        @Feature: Content Hosts

        @Assert: Content host is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_content_host({
                u'name': test_data['name'],
                u'organization-id': self.NEW_ORG['id'],
                u'content-view-id': self.DEFAULT_CV['id'],
                u'lifecycle-environment-id': self.LIBRARY['id'],
            })

    @run_only_on('sat')
    def test_negative_create_2(self):
        """@Test: Check if content host can be created with new content view

        @Feature: Content Hosts

        @Assert: Content host is not created using new unpublished cv

        """
        con_view = make_content_view(
            {u'organization-id': TestContentHost.NEW_ORG['id']}
        )
        with self.assertRaises(CLIFactoryError):
            env = TestContentHost.NEW_LIFECYCLE['id']
            make_content_host({
                u'name': gen_string('alpha', 15),
                u'organization-id': TestContentHost.NEW_ORG['id'],
                u'content-view-id': con_view['id'],
                u'lifecycle-environment-id': env,
            })

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Check if content host name can be updated

        @Feature: Content Hosts

        @Assert: Content host is created and name is updated

        """
        new_system = None
        try:
            new_system = make_content_host({
                u'organization-id': self.NEW_ORG['id'],
                u'content-view-id': self.DEFAULT_CV['id'],
                u'lifecycle-environment-id': self.LIBRARY['id']})
        except CLIFactoryError as err:
            self.fail(err)
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
        {u'description': gen_string('alpha', 15)},
        {u'description': gen_string('alphanumeric', 15)},
        {u'description': gen_string('numeric', 15)},
        {u'description': gen_string('latin1', 15)},
        {u'description': gen_string('utf8', 15)},
        {u'description': gen_string('html', 15)},
    )
    def test_positive_update_2(self, test_data):
        """@Test: Check if content host description can be updated

        @Feature: Content Hosts

        @Assert: Content host is created and description is updated

        """

        new_system = make_content_host({
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id']})
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
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_delete_1(self, test_data):
        """@Test: Check if content host can be created and deleted

        @Feature: Content Hosts

        @Assert: Content host is created and then deleted

        """

        new_system = make_content_host({
            u'name': test_data['name'],
            u'organization-id': self.NEW_ORG['id'],
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id']})
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

    @skip_if_bug_open('bugzilla', 1154611)
    def test_bugzilla_1154611(self):
        """@test: check if Content Host creation does not allow duplicated names

        @feature: Contet_Hosts

        @assert: Content Hosts with the same name are not allowed

        @bz: 1154611

        """
        name = gen_string('alpha', 15)
        try:
            result = make_content_host({
                u'name': name,
                u'organization-id': self.NEW_ORG['id'],
                u'content-view-id': self.DEFAULT_CV['id'],
                u'lifecycle-environment-id': self.LIBRARY['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(result['name'], name)

        with self.assertRaises(CLIFactoryError):
            make_content_host({
                u'name': name,
                u'organization-id': self.NEW_ORG['id'],
                u'content-view-id': self.DEFAULT_CV['id'],
                u'lifecycle-environment-id': self.LIBRARY['id'],
            })


class TestContentHostKatelloAgent(CLITestCase):
    """Content-host tests, which require VM with installed katello-agent."""

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages

        """
        super(TestContentHostKatelloAgent, self).setUp()
        # Create new org and environment
        self.org = make_org()
        self.env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Clone manifest and upload it
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Enable repo from Repository Set
        result = RepositorySet.enable({
            u'name': REPOSET['rhst7'],
            u'organization-id': self.org['id'],
            u'product': PRDS['rhel'],
            u'releasever': '7Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        # Fetch repository info
        result = Repository.info({
            u'name': REPOS['rhst7']['name'],
            u'product': PRDS['rhel'],
            u'organization-id': self.org['id'],
        })
        rhel_repo = result.stdout
        # Synchronize the RH repository
        result = Repository.synchronize({
            u'name': REPOS['rhst7']['name'],
            u'organization-id': self.org['id'],
            u'product': PRDS['rhel'],
        })
        self.assertEqual(result.return_code, 0)
        # Create CV and associate repo with it
        self.cv = make_content_view({u'organization-id': self.org['id']})
        result = ContentView.add_repository({
            u'id': self.cv['id'],
            u'repository-id': rhel_repo['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Publish a version1 of CV
        result = ContentView.publish({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        # Get the version1 id
        result = ContentView.info({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        # Promote version1 to next env
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': self.env['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Create activation key
        self.activation_key = make_activation_key({
            u'lifecycle-environment-id': self.env['id'],
            u'organization-id': self.org['id'],
            u'content-view': self.cv['name'],
        })
        # List the subscriptions in given org
        result = Subscription.list(
            {u'organization-id': self.org['id']},
            per_page=False
        )
        self.assertEqual(result.return_code, 0)
        # Add subscription to activation-key
        for subscription in result.stdout:
            if subscription['name'] == DEFAULT_SUBSCRIPTION_NAME:
                self.assertGreater(int(subscription['quantity']), 0)
                result = ActivationKey.add_subscription({
                    u'id': self.activation_key['id'],
                    u'subscription-id': subscription['id'],
                    u'quantity': 1,
                })
                self.assertEqual(result.return_code, 0)
        # Create VM
        self.vm = VirtualMachine(distro='rhel71')
        self.vm.create()
        # Download and Install katello-ca rpm
        result = self.vm.run(
            'wget -nd -r -l1 --no-parent -A \'*.noarch.rpm\' http://{0}/pub/'
            .format(conf.properties['main.server.hostname'])
        )
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -i katello-ca-consumer*.noarch.rpm')
        self.assertEqual(result.return_code, 0)
        # Register client with foreman server using activation-key
        result = self.vm.run(
            'subscription-manager register --activationkey {0} '
            '--org {1} --force'
            .format(self.activation_key['name'], self.org['label'])
        )
        self.assertEqual(result.return_code, 0)
        # Enable Red Hat Satellite Tools repo
        result = self.vm.run(
            'subscription-manager repos --enable {0}'
            .format(REPOS['rhst7']['id'])
        )
        self.assertEqual(result.return_code, 0)
        # Install katello-agent package
        result = self.vm.run('yum install -y katello-agent')
        self.assertEqual(result.return_code, 0)
        # Verify if package is installed by query it
        result = self.vm.run('rpm -q katello-agent')
        self.assertIn('katello-agent', result.stdout[0])

    def tearDown(self):
        self.vm.destroy()
        super(TestContentHostKatelloAgent, self).tearDown()

    @run_only_on('sat')
    def test_contenthost_get_errata_info(self):
        """@Test: Get errata info

        @Feature: Content Host - Errata

        @Assert: Errata info was displayed

        """
        # Create custom product and repository
        custom_product = make_product({u'organization-id': self.org['id']})
        custom_repo = make_repository({
            u'url': FAKE_0_YUM_REPO,
            u'content-type': 'yum',
            u'product-id': custom_product['id'],
        })
        # Synchronize custom repository
        result = Repository.synchronize({'id': custom_repo['id']})
        self.assertEqual(result.return_code, 0)
        # Associate repo with CV
        result = ContentView.add_repository({
            u'id': self.cv['id'],
            u'repository-id': custom_repo['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Publish a new version of CV
        result = ContentView.publish({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        # Get the version id
        result = ContentView.info({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][-1]
        # Promote version to next env
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': self.env['id'],
        })
        self.assertEqual(result.return_code, 0)
        # List the subscriptions in given org
        result = Subscription.list(
            {u'organization-id': self.org['id']},
            per_page=False
        )
        self.assertEqual(result.return_code, 0)
        # Add subscription to activation-key
        for subscription in result.stdout:
            if subscription['name'] == custom_product['name']:
                self.assertNotEqual(int(subscription['quantity']), 0)
                result = ActivationKey.add_subscription({
                    u'id': self.activation_key['id'],
                    u'subscription-id': subscription['id'],
                })
                self.assertEqual(result.return_code, 0)
        # Install custom package
        result = self.vm.run(
            'wget -nd -r -l1 --no-parent -A \'{0}.rpm\' {1}'
            .format(FAKE_0_CUSTOM_PACKAGE, FAKE_0_YUM_REPO)
        )
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -i {0}.rpm'.format(FAKE_0_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        # Get errata info
        result = ContentHost.errata_info({
            u'organization-id': self.org['id'],
            u'content-host': self.vm.target_image,
            u'id': FAKE_0_ERRATA_ID,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout[0]['errata-id'], FAKE_0_ERRATA_ID)
        self.assertEqual(result.stdout[0]['packages'], FAKE_0_CUSTOM_PACKAGE)

    @run_only_on('sat')
    def test_contenthost_apply_errata(self):
        """@Test: Apply errata to content host

        @Feature: Content Host - Errata

        @Assert: Errata is scheduled for installation

        """
        # Create custom product and repository
        custom_product = make_product({u'organization-id': self.org['id']})
        custom_repo = make_repository({
            u'url': FAKE_0_YUM_REPO,
            u'content-type': 'yum',
            u'product-id': custom_product['id'],
        })
        # Synchronize custom repository
        result = Repository.synchronize({'id': custom_repo['id']})
        self.assertEqual(result.return_code, 0)
        # Associate repo with CV
        result = ContentView.add_repository({
            u'id': self.cv['id'],
            u'repository-id': custom_repo['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Publish a new version of CV
        result = ContentView.publish({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        # Get the version id
        result = ContentView.info({u'id': self.cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][-1]
        # Promote version to next env
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': self.env['id'],
        })
        self.assertEqual(result.return_code, 0)
        # List the subscriptions in given org
        result = Subscription.list(
            {u'organization-id': self.org['id']},
            per_page=False
        )
        self.assertEqual(result.return_code, 0)
        # Add subscription to activation-key
        for subscription in result.stdout:
            if subscription['name'] == custom_product['name']:
                self.assertNotEqual(int(subscription['quantity']), 0)
                result = ActivationKey.add_subscription({
                    u'id': self.activation_key['id'],
                    u'subscription-id': subscription['id'],
                })
                self.assertEqual(result.return_code, 0)
        # Install custom package
        result = self.vm.run(
            'wget -nd -r -l1 --no-parent -A \'{0}.rpm\' {1}'
            .format(FAKE_0_CUSTOM_PACKAGE, FAKE_0_YUM_REPO)
        )
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -i {0}.rpm'.format(FAKE_0_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        # Apply errata to content host
        result = ContentHost.errata_apply({
            u'organization-id': self.org['id'],
            u'content-host': self.vm.target_image,
            u'errata-ids': FAKE_0_ERRATA_ID,
        })
        self.assertEqual(result.return_code, 0)
