"""Test class for Content-Host CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
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
from robottelo.datafactory import invalid_values_list, generate_strings_list
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


class TestContentHost(CLITestCase):
    """content-host CLI tests."""

    NEW_ORG = None
    NEW_CV = None
    PROMOTED_CV = None
    NEW_LIFECYCLE = None
    LIBRARY = None
    DEFAULT_CV = None

    # pylint: disable=unexpected-keyword-arg
    @classmethod
    def setUpClass(cls):
        """Tests for Content Host via Hammer CLI"""
        super(TestContentHost, cls).setUpClass()
        TestContentHost.NEW_ORG = make_org(cached=True)
        TestContentHost.NEW_LIFECYCLE = make_lifecycle_environment(
            {u'organization-id': TestContentHost.NEW_ORG['id']},
            cached=True
        )
        TestContentHost.LIBRARY = LifecycleEnvironment.info({
            u'organization-id': TestContentHost.NEW_ORG['id'],
            u'name': u'Library',
        })
        TestContentHost.DEFAULT_CV = ContentView.info({
            u'organization-id': TestContentHost.NEW_ORG['id'],
            u'name': u'Default Organization View',
        })
        TestContentHost.NEW_CV = make_content_view({
            u'organization-id': TestContentHost.NEW_ORG['id'],
        })
        cv_id = TestContentHost.NEW_CV['id']
        ContentView.publish({u'id': cv_id})
        version_id = ContentView.version_list({
            u'content-view-id': cv_id,
        })[0]['id']
        ContentView.version_promote({
            u'id': version_id,
            u'to-lifecycle-environment-id': TestContentHost.NEW_LIFECYCLE[
                'id'
            ],
            u'organization-id': TestContentHost.NEW_ORG['id']
        })
        TestContentHost.PROMOTED_CV = TestContentHost.NEW_CV

    def test_positive_create_1(self):
        """@Test: Check if content host can be created with random names

        @Feature: Content Hosts

        @Assert: Content host is created and has random name

        """
        for name in generate_strings_list(15):
            with self.subTest(name):
                new_system = make_content_host({
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'name': name,
                    u'organization-id': self.NEW_ORG['id'],
                })
            # Assert that name matches data passed
            self.assertEqual(new_system['name'], name)

    def test_positive_create_2(self):
        """@Test: Check if content host can be created with random description

        @Feature: Content Hosts

        @Assert: Content host is created and has random description

        """
        for desc in generate_strings_list(15):
            with self.subTest(desc):
                new_system = make_content_host({
                    u'description': desc,
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'organization-id': self.NEW_ORG['id'],
                })
                # Assert that description matches data passed
                self.assertEqual(new_system['description'], desc)

    def test_positive_create_3(self):
        """@Test: Check if content host can be created with organization name

        @Feature: Content Hosts

        @Assert: Content host is created using organization name

        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': gen_string('alpha', 15),
            u'organization': self.NEW_ORG['name'],
        })
        # Info does not tell us information about the organization so
        # let's assert that content view and environments match instead
        self.assertEqual(new_system['content-view'], self.DEFAULT_CV['name'])
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
        )

    def test_positive_create_4(self):
        """@Test: Check if content host can be created with organization label

        @Feature: Content Hosts

        @Assert: Content host is created using organization label

        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': gen_string('alpha', 15),
            u'organization-label': self.NEW_ORG['label'],
        })
        # Info does not tell us information about the organization so
        # let's assert that content view and environments match instead
        self.assertEqual(new_system['content-view'], self.DEFAULT_CV['name'])
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
        )

    @run_only_on('sat')
    def test_positive_create_5(self):
        """@Test: Check if content host can be created with content view name

        @Feature: Content Hosts

        @Assert: Content host is created using content view name

        """
        new_system = make_content_host({
            u'content-view': self.DEFAULT_CV['name'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
        })
        # Assert that name matches data passed
        self.assertEqual(new_system['content-view'], self.DEFAULT_CV['name'])

    @run_only_on('sat')
    def test_positive_create_6(self):
        """@Test: Check if content host can be created with lifecycle name

        @Feature: Content Hosts

        @Assert: Content host is created using lifecycle name

        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment': self.LIBRARY['name'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
        })
        # Assert that lifecycles matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
        )

    @run_only_on('sat')
    def test_positive_create_7(self):
        """@Test: Check if content host can be created with new lifecycle

        @Feature: Content Hosts

        @Assert: Content host is created using new lifecycle

        """
        new_system = make_content_host({
            u'content-view-id': self.PROMOTED_CV['id'],
            u'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
        })
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.NEW_LIFECYCLE['name'],
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
            u'content-view-id': TestContentHost.PROMOTED_CV['id'],
            u'lifecycle-environment-id': TestContentHost.NEW_LIFECYCLE['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': TestContentHost.NEW_ORG['id'],
        })
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['content-view'],
            TestContentHost.PROMOTED_CV['name'],
        )

    def test_negative_create_1(self):
        """@Test: Check if content host can be created with random long names

        @Feature: Content Hosts

        @Assert: Content host is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_content_host({
                        u'name': name,
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
        con_view = make_content_view({
            u'organization-id': TestContentHost.NEW_ORG['id'],
        })
        env = TestContentHost.NEW_LIFECYCLE['id']
        with self.assertRaises(CLIFactoryError):
            make_content_host({
                u'content-view-id': con_view['id'],
                u'lifecycle-environment-id': env,
                u'name': gen_string('alpha', 15),
                u'organization-id': TestContentHost.NEW_ORG['id'],
            })

    def test_positive_update_1(self):
        """@Test: Check if content host name can be updated

        @Feature: Content Hosts

        @Assert: Content host is created and name is updated

        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'organization-id': self.NEW_ORG['id'],
        })
        for new_name in generate_strings_list():
            with self.subTest(new_name):
                ContentHost.update({
                    u'id': new_system['id'],
                    u'name': new_name,
                })
                result = ContentHost.info({'id': new_system['id']})
                self.assertEqual(result['name'], new_name)

    def test_positive_update_2(self):
        """@Test: Check if content host description can be updated

        @Feature: Content Hosts

        @Assert: Content host is created and description is updated

        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'organization-id': self.NEW_ORG['id'],
        })
        for new_desc in generate_strings_list():
            with self.subTest(new_desc):
                ContentHost.update({
                    u'id': new_system['id'],
                    u'description': new_desc,
                })
                result = ContentHost.info({'id': new_system['id']})
                self.assertEqual(result['description'], new_desc)

    def test_positive_delete_1(self):
        """@Test: Check if content host can be created and deleted

        @Feature: Content Hosts

        @Assert: Content host is created and then deleted

        """
        for name in generate_strings_list():
            with self.subTest(name):
                new_system = make_content_host({
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'name': name,
                    u'organization-id': self.NEW_ORG['id'],
                })
                ContentHost.delete({u'id': new_system['id']})
                with self.assertRaises(CLIReturnCodeError):
                    ContentHost.info({'id': new_system['id']})

    @skip_if_bug_open('bugzilla', 1154611)
    def test_bugzilla_1154611(self):
        """@test: check if Content Host creation does not allow duplicated
        names

        @feature: Contet_Hosts

        @assert: Content Hosts with the same name are not allowed

        @bz: 1154611

        """
        name = gen_string('alpha', 15)
        result = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': name,
            u'organization-id': self.NEW_ORG['id'],
        })
        self.assertEqual(result['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_content_host({
                u'content-view-id': self.DEFAULT_CV['id'],
                u'lifecycle-environment-id': self.LIBRARY['id'],
                u'name': name,
                u'organization-id': self.NEW_ORG['id'],
            })


class TestCHKatelloAgent(CLITestCase):
    """Content-host tests, which require VM with installed katello-agent."""

    org = None
    env = None
    content_view = None
    activation_key = None

    @classmethod
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key

        """
        super(TestCHKatelloAgent, cls).setUpClass()
        # Create new org, environment, CV and activation key
        TestCHKatelloAgent.org = make_org()
        TestCHKatelloAgent.env = make_lifecycle_environment({
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        TestCHKatelloAgent.content_view = make_content_view({
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        TestCHKatelloAgent.activation_key = make_activation_key({
            u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        # Add subscription to Satellite Tools repo to activation key
        setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-view-id': TestCHKatelloAgent.content_view['id'],
            u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
            u'activationkey-id': TestCHKatelloAgent.activation_key['id'],
        })
        # Create custom repo, add subscription to activation key
        setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'content-view-id': TestCHKatelloAgent.content_view['id'],
            u'lifecycle-environment-id': TestCHKatelloAgent.env['id'],
            u'activationkey-id': TestCHKatelloAgent.activation_key['id'],
        })

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages

        """
        super(TestCHKatelloAgent, self).setUp()
        # Create VM and register content host
        self.client = VirtualMachine(distro='rhel71')
        self.client.create()
        self.client.install_katello_cert()
        # Register content host, install katello-agent
        self.client.register_contenthost(
            TestCHKatelloAgent.activation_key['name'],
            TestCHKatelloAgent.org['label']
        )
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    def tearDown(self):
        self.client.destroy()
        super(TestCHKatelloAgent, self).tearDown()

    @run_only_on('sat')
    def test_ch_get_errata_info(self):
        """@Test: Get errata info

        @Feature: Content Host - Errata

        @Assert: Errata info was displayed

        """
        self.client.download_install_rpm(
            FAKE_0_YUM_REPO,
            FAKE_0_CUSTOM_PACKAGE
        )
        result = ContentHost.errata_info({
            u'content-host': self.client.hostname,
            u'id': FAKE_0_ERRATA_ID,
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        self.assertEqual(result[0]['errata-id'], FAKE_0_ERRATA_ID)
        self.assertEqual(result[0]['packages'], FAKE_0_CUSTOM_PACKAGE)

    @run_only_on('sat')
    def test_ch_apply_errata(self):
        """@Test: Apply errata to content host

        @Feature: Content Host - Errata

        @Assert: Errata is scheduled for installation

        """
        self.client.download_install_rpm(
            FAKE_0_YUM_REPO,
            FAKE_0_CUSTOM_PACKAGE
        )
        ContentHost.errata_apply({
            u'content-host': self.client.hostname,
            u'errata-ids': FAKE_0_ERRATA_ID,
            u'organization-id': TestCHKatelloAgent.org['id'],
        })

    @run_only_on('sat')
    def test_ch_package_install(self):
        """@Test: Install package to content host remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully installed

        """
        ContentHost.package_install({
            u'content-host': self.client.hostname,
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'packages': FAKE_0_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME)
        )
        self.assertEqual(result.return_code, 0)

    @run_only_on('sat')
    def test_ch_package_remove(self):
        """@Test: Remove package from content host remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully removed

        """
        self.client.download_install_rpm(
            FAKE_0_YUM_REPO,
            FAKE_0_CUSTOM_PACKAGE
        )
        ContentHost.package_remove({
            u'content-host': self.client.hostname,
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'packages': FAKE_0_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run(
            'rpm -q {0}'.format(FAKE_0_CUSTOM_PACKAGE_NAME)
        )
        self.assertNotEqual(result.return_code, 0)

    @run_only_on('sat')
    def test_ch_package_upgrade(self):
        """@Test: Upgrade content host package remotely

        @Feature: Content Host - Package

        @Assert: Package was successfully upgraded

        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        ContentHost.package_upgrade({
            u'content-host': self.client.hostname,
            u'organization-id': TestCHKatelloAgent.org['id'],
            u'packages': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    @run_only_on('sat')
    def test_ch_package_upgrade_all(self):
        """@Test: Upgrade all the content host packages remotely

        @Feature: Content Host - Package

        @Assert: Packages (at least 1 with newer version available) were
        successfully upgraded

        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        ContentHost.package_upgrade_all({
            u'content-host': self.client.hostname,
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        result = self.client.run('rpm -q {0}'.format(FAKE_2_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)

    @run_only_on('sat')
    def test_ch_package_group_install(self):
        """@Test: Install package group to content host remotely

        @Feature: Content Host - Package group

        @Assert: Package group was successfully installed

        """
        ContentHost.package_group_install({
            u'content-host': self.client.hostname,
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            u'organization-id': TestCHKatelloAgent.org['id'],
        })
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run('rpm -q {0}'.format(package))
            self.assertEqual(result.return_code, 0)

    @run_only_on('sat')
    def test_ch_package_group_remove(self):
        """@Test: Remove package group from content host remotely

        @Feature: Content Host - Package group

        @Assert: Package group was successfully removed

        """
        hammer_args = {
            u'content-host': self.client.hostname,
            u'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            u'organization-id': TestCHKatelloAgent.org['id'],
        }
        ContentHost.package_group_install(hammer_args)
        ContentHost.package_group_remove(hammer_args)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run('rpm -q {0}'.format(package))
            self.assertNotEqual(result.return_code, 0)
