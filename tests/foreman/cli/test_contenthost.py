"""Test class for Content-Host CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_host,
    make_content_view,
    make_lifecycle_environment,
    make_org,
)
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_hosts_list,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier3,
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


class ContentHostTestCase(CLITestCase):
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
        super(ContentHostTestCase, cls).setUpClass()
        ContentHostTestCase.NEW_ORG = make_org(cached=True)
        ContentHostTestCase.NEW_LIFECYCLE = make_lifecycle_environment(
            {u'organization-id': ContentHostTestCase.NEW_ORG['id']},
            cached=True
        )
        ContentHostTestCase.LIBRARY = LifecycleEnvironment.info({
            u'organization-id': ContentHostTestCase.NEW_ORG['id'],
            u'name': u'Library',
        })
        ContentHostTestCase.DEFAULT_CV = ContentView.info({
            u'organization-id': ContentHostTestCase.NEW_ORG['id'],
            u'name': u'Default Organization View',
        })
        ContentHostTestCase.NEW_CV = make_content_view({
            u'organization-id': ContentHostTestCase.NEW_ORG['id'],
        })
        cv_id = ContentHostTestCase.NEW_CV['id']
        ContentView.publish({u'id': cv_id})
        version_id = ContentView.version_list({
            u'content-view-id': cv_id,
        })[0]['id']
        ContentView.version_promote({
            u'id': version_id,
            u'to-lifecycle-environment-id': ContentHostTestCase.NEW_LIFECYCLE[
                'id'
            ],
            u'organization-id': ContentHostTestCase.NEW_ORG['id']
        })
        ContentHostTestCase.PROMOTED_CV = ContentHostTestCase.NEW_CV

    @tier1
    def test_positive_create_with_name(self):
        """Check if content host can be created with random names

        @Feature: Content Hosts

        @Assert: Content host is created and has random name
        """
        for name in valid_hosts_list():
            with self.subTest(name):
                new_system = make_content_host({
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'name': name,
                    u'organization-id': self.NEW_ORG['id'],
                })
            # Assert that name matches data passed
            self.assertEqual(new_system['name'], name)

    @tier1
    def test_positive_create_with_org_name(self):
        """Check if content host can be created with organization name

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

    @tier1
    def test_positive_create_with_org_label(self):
        """Check if content host can be created with organization label

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
    @tier1
    def test_positive_create_with_cv_default(self):
        """Check if content host can be created with content view name

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

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_lce_library(self):
        """Check if content host can be created with lifecycle name

        @Feature: Content Hosts

        @Assert: Content host is created using lifecycle name
        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment': self.LIBRARY['name'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.NEW_ORG['id'],
        })
        # Assert that lifecycle envs matches data passed
        self.assertEqual(
            new_system['lifecycle-environment'],
            self.LIBRARY['name'],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_lce(self):
        """Check if content host can be created with new lifecycle

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

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_cv(self):
        """Check if content host can be created with new content view

        @Feature: Content Hosts

        @Assert: Content host is created using new published, promoted cv
        """
        if ContentHostTestCase.PROMOTED_CV is None:
            self.fail("Couldn't prepare promoted contentview for this test")

        new_system = make_content_host({
            u'content-view-id': ContentHostTestCase.PROMOTED_CV['id'],
            u'lifecycle-environment-id':
                ContentHostTestCase.NEW_LIFECYCLE['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': ContentHostTestCase.NEW_ORG['id'],
        })
        # Assert that content views matches data passed
        self.assertEqual(
            new_system['content-view'],
            ContentHostTestCase.PROMOTED_CV['name'],
        )

    @tier1
    def test_negative_create_with_name(self):
        """Check if content host can be created with random long names

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

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_unpublished_cv(self):
        """Check if content host can be created using unpublished cv

        @Feature: Content Hosts

        @Assert: Content host is not created using new unpublished cv
        """
        cv = make_content_view({
            u'organization-id': ContentHostTestCase.NEW_ORG['id'],
        })
        env = ContentHostTestCase.NEW_LIFECYCLE['id']
        with self.assertRaises(CLIFactoryError):
            make_content_host({
                u'content-view-id': cv['id'],
                u'lifecycle-environment-id': env,
                u'name': gen_string('alpha', 15),
                u'organization-id': ContentHostTestCase.NEW_ORG['id'],
            })

    @tier1
    @skip_if_bug_open('bugzilla', 1318686)
    def test_positive_update_name(self):
        """Check if content host name can be updated

        @Feature: Content Hosts

        @Assert: Content host is created and name is updated

        @BZ: 1318686
        """
        new_system = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'organization-id': self.NEW_ORG['id'],
        })
        for new_name in valid_hosts_list():
            with self.subTest(new_name):
                ContentHost.update({
                    u'id': new_system['id'],
                    u'new-name': new_name,
                })
                result = ContentHost.info({'id': new_system['id']})
                self.assertEqual(result['name'], new_name)

    @tier1
    @skip_if_bug_open('bugzilla', 1328202)
    def test_positive_delete_by_id(self):
        """Check if content host can be created and deleted by passing its ID

        @Feature: Content Hosts

        @Assert: Content host is created and then deleted

        @BZ: 1328202
        """
        for name in generate_strings_list():
            with self.subTest(name):
                content_host = make_content_host({
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'name': name,
                    u'organization-id': self.NEW_ORG['id'],
                })
                ContentHost.delete({u'host-id': content_host['id']})
                with self.assertRaises(CLIReturnCodeError):
                    ContentHost.info({'id': content_host['id']})

    @tier1
    def test_positive_delete_by_name(self):
        """Check if content host can be created and deleted by passing its name

        @Feature: Content Hosts

        @Assert: Content host is created and then deleted
        """
        for name in valid_hosts_list():
            with self.subTest(name):
                content_host = make_content_host({
                    u'content-view-id': self.DEFAULT_CV['id'],
                    u'lifecycle-environment-id': self.LIBRARY['id'],
                    u'name': name,
                    u'organization-id': self.NEW_ORG['id'],
                })
                ContentHost.delete({u'host': content_host['name']})
                with self.assertRaises(CLIReturnCodeError):
                    ContentHost.info({'id': content_host['id']})

    @tier1
    def test_negative_create_with_same_name(self):
        """Check if Content Host creation does not allow duplicated
        names

        @Feature: Content Hosts

        @Assert: Content Hosts with the same name are not allowed
        """
        name = gen_string('alpha', 15).lower()
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

    @tier3
    def test_positive_register_with_no_ak(self):
        """Register Content host to satellite without activation key

        @Feature: Content Hosts

        @Assert: Content host successfully registered to appropriate org
        """
        with VirtualMachine(distro='rhel71') as client:
            client.install_katello_ca()
            result = client.run(
                u'subscription-manager register --org {0} '
                '--environment {1}/{2} --username {3} --password {4}'
                .format(
                    self.NEW_ORG['label'],
                    self.NEW_LIFECYCLE['label'],
                    self.PROMOTED_CV['label'],
                    self.katello_user,
                    self.katello_passwd
                )
            )
            self.assertEqual(result.return_code, 0)

    @tier3
    def test_negative_register_twice(self):
        """Attempt to register a Content host twice to Satellite

        @Feature: Content Hosts

        @Assert: Content host cannot be registered twice
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro='rhel71') as client:
            client.install_katello_ca()
            client.register_contenthost(
                activation_key['name'],
                self.NEW_ORG['label'],
            )
            result = client.register_contenthost(
                activation_key['name'],
                self.NEW_ORG['label'],
                force=False,
            )
            # Depending on distro version, successful return_code may be 0 or
            # 1, so we can't verify CH wasn't registered by return_code != 0
            # check. Verifying return_code == 64 here, which stands for content
            # host being already registered.
            self.assertEqual(result.return_code, 64)

    @tier3
    def test_positive_list(self):
        """List Content hosts for a given org

        @Feature: Content Hosts

        @Assert: Content hosts are listed for the given org
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro='rhel71') as client:
            client.install_katello_ca()
            client.register_contenthost(
                activation_key['name'],
                self.NEW_ORG['label'],
            )
            result = ContentHost.list({
                'organization-id': self.NEW_ORG['id'],
                'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            })
            self.assertGreaterEqual(len(result), 1)
            self.assertIn(client.hostname, [chost['name'] for chost in result])

    @tier3
    def test_positive_unregister(self):
        """Unregister Content host

        @Feature: Content Hosts

        @Assert: After unregistering, content hosts list for the org does not
        show the content host
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro='rhel71') as client:
            client.install_katello_ca()
            client.register_contenthost(
                activation_key['name'],
                self.NEW_ORG['label'],
            )
            result = ContentHost.list({
                'organization-id': self.NEW_ORG['id'],
                'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            })
            self.assertGreaterEqual(len(result), 1)
            self.assertIn(client.hostname, [chost['name'] for chost in result])
            result = client.run('subscription-manager unregister')
            self.assertEqual(result.return_code, 0)
            result = ContentHost.list({
                'organization-id': self.NEW_ORG['id'],
                'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            })
            self.assertNotIn(
                client.hostname, [chost['name'] for chost in result])
