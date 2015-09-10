# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for Content-Host CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
    make_content_host,
    make_content_view,
    make_lifecycle_environment,
    make_org,
)
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_0_ERRATA_ID,
    FAKE_0_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import data, run_only_on, skip_if_bug_open
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
            result = LifecycleEnvironment.info({
                u'organization-id': TestContentHost.NEW_ORG['id'],
                u'name': u'Library',
            })
            self.assertEqual(result.return_code, 0)
            TestContentHost.LIBRARY = result.stdout
        if TestContentHost.DEFAULT_CV is None:
            result = ContentView.info({
                u'organization-id': TestContentHost.NEW_ORG['id'],
                u'name': u'Default Organization View',
            })
            self.assertEqual(result.return_code, 0)
            TestContentHost.DEFAULT_CV = result.stdout
        if TestContentHost.NEW_CV is None:
            TestContentHost.NEW_CV = make_content_view({
                u'organization-id': TestContentHost.NEW_ORG['id'],
            })
            TestContentHost.PROMOTED_CV = None
            cv_id = TestContentHost.NEW_CV['id']
            result = ContentView.publish({u'id': cv_id})
            self.assertEqual(result.return_code, 0)
            result = ContentView.version_list({u'content-view-id': cv_id})
            self.assertEqual(result.return_code, 0)
            version_id = result.stdout[0]['id']
            result = ContentView.version_promote({
                u'id': version_id,
                u'to-lifecycle-environment-id': TestContentHost.NEW_LIFECYCLE[
                    'id'],
                u'organization-id': TestContentHost.NEW_ORG['id']
            })
            self.assertEqual(result.return_code, 0)
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


@run_only_on('sat')
class TestCHKatelloAgent(CLITestCase):
    """Content-host tests, which require VM with installed katello-agent."""

    org = None
    env = None
    cv = None
    activation_key = None
    org_is_set_up = False

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages

        """
        super(TestCHKatelloAgent, self).setUp()

        # Create new org, environment, CV and activation key
        if TestCHKatelloAgent.org is None:
            TestCHKatelloAgent.org = make_org()
        if TestCHKatelloAgent.env is None:
            TestCHKatelloAgent.env = make_lifecycle_environment({
                u'organization-id': TestCHKatelloAgent.org['id'],
            })
        if TestCHKatelloAgent.cv is None:
            TestCHKatelloAgent.cv = make_content_view({
                u'organization-id': TestCHKatelloAgent.org['id'],
            })
        if TestCHKatelloAgent.activation_key is None:
            TestCHKatelloAgent.activation_key = make_activation_key({
                u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
                u'organization-id': TestCHKatelloAgent.org['id'],
            })
        # Add subscription to Satellite Tools repo to activation key
        if not TestCHKatelloAgent.org_is_set_up:
            setup_org_for_a_rh_repo({
                u'product': PRDS['rhel'],
                u'repository-set': REPOSET['rhst7'],
                u'repository': REPOS['rhst7']['name'],
                u'organization-id': TestCHKatelloAgent.org['id'],
                u'content-view-id': TestCHKatelloAgent.cv['id'],
                u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
                u'activationkey-id': TestCHKatelloAgent.activation_key['id'],
            })
            TestCHKatelloAgent.org_is_set_up = True

        # Create VM and register content host
        self.vm = VirtualMachine(distro='rhel71')
        self.vm.create()
        self.vm.install_katello_cert()
        # Create custom repo, add subscription to activation key
        setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-view-id': TestCHKatelloAgent.cv['id'],
            u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
            u'activationkey-id': TestCHKatelloAgent.activation_key['id'],
        })
        # Register content host, install katello-agent
        self.vm.register_contenthost(
            TestCHKatelloAgent.activation_key['name'],
            TestCHKatelloAgent.org['label']
        )
        self.vm.enable_repo(REPOS['rhst7']['id'])
        self.vm.install_katello_agent()

    def tearDown(self):
        self.vm.destroy()
        super(TestCHKatelloAgent, self).tearDown()

    def test_contenthost_get_errata_info(self):
        """@Test: Get errata info

        @Feature: Content Host - Errata

        @Assert: Errata info was displayed

        """
        self.vm.download_install_rpm(FAKE_0_YUM_REPO, FAKE_0_CUSTOM_PACKAGE)
        result = ContentHost.errata_info({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'id': FAKE_0_ERRATA_ID,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout[0]['errata-id'], FAKE_0_ERRATA_ID)
        self.assertEqual(result.stdout[0]['packages'], FAKE_0_CUSTOM_PACKAGE)

    def test_contenthost_apply_errata(self):
        """@Test: Apply errata to content host

        @Feature: Content Host - Errata

        @Assert: Errata is scheduled for installation

        """
        self.vm.download_install_rpm(FAKE_0_YUM_REPO, FAKE_0_CUSTOM_PACKAGE)
        result = ContentHost.errata_apply({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'errata-ids': FAKE_0_ERRATA_ID,
        })
        self.assertEqual(result.return_code, 0)

    def test_contenthost_package_install(self):
        """@Test: Install package to content host remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully installed

        """
        result = ContentHost.package_install({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'packages': FAKE_0_CUSTOM_PACKAGE_NAME,
        })
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -q {}'.format(FAKE_0_CUSTOM_PACKAGE_NAME))
        self.assertEqual(result.return_code, 0)

    def test_contenthost_package_remove(self):
        """@Test: Remove package from content host remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully removed

        """
        self.vm.download_install_rpm(FAKE_0_YUM_REPO, FAKE_0_CUSTOM_PACKAGE)
        result = ContentHost.package_remove({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'packages': FAKE_0_CUSTOM_PACKAGE_NAME,
        })
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -q {}'.format(FAKE_0_CUSTOM_PACKAGE_NAME))
        self.assertNotEqual(result.return_code, 0)

    def test_contenthost_package_upgrade(self):
        """@Test: Upgrade content host package remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully upgraded

        """
        self.vm.run('yum install -y {}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = ContentHost.package_upgrade({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'packages': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -q {}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    def test_contenthost_package_upgrade_all(self):
        """@Test: Upgrade all the content host packages remotely

        @Feature: Content Host - Package

        @Assert: Packages (at least 1 with newer version available) were
        successfully upgraded

        """
        self.vm.run('yum install -y {}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = ContentHost.package_upgrade_all({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
        })
        self.assertEqual(result.return_code, 0)
        result = self.vm.run('rpm -q {}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    def test_contenthost_package_group_install(self):
        """@Test: Install package group to content host remotely

        @Feature: Content Host - Package group

        @Assert: Package group was successfully installed

        """
        result = ContentHost.package_group_install({
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
        })
        self.assertEqual(result.return_code, 0)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.vm.run('rpm -q {}'.format(package))
            self.assertEqual(result.return_code, 0)

    def test_contenthost_package_group_remove(self):
        """@Test: Remove package group from content host remotely

        @Feature: Content Host - Package group

        @Assert: Package group was successfully removed

        """
        hammer_args = {
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-host': self.vm.hostname,
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
        }
        result = ContentHost.package_group_install(hammer_args)
        self.assertEqual(result.return_code, 0)
        result = ContentHost.package_group_remove(hammer_args)
        self.assertEqual(result.return_code, 0)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.vm.run('rpm -q {}'.format(package))
            self.assertNotEqual(result.return_code, 0)
