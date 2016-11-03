"""Test class for Content-Host CLI

@Requirement: Contenthost

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

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
from robottelo.constants import DISTRO_RHEL7
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.datafactory import (
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

        @id: ad2b1b03-68a1-49c8-9523-4164fcd7ee14

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

        @id: c08b0dac-9820-4261-bb0b-8a78f5c78a74

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

        @id: 4723e735-3a14-4ebd-83c1-30be065f4b42

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

        @id: bb69a70e-17f9-4639-802d-90e6a4520afa

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

        @id: 0093be1c-3664-448e-87f5-758bab34958a

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

        @id: e102b034-0011-471d-ba21-5ef8d129a61f

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

        @id: f90873b9-fb3a-4c93-8647-4b1aea0a2c35

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

        @id: f92b6070-b2d1-4e3e-975c-39f1b1096697

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

        @id: 9997383d-3c27-4f14-94f9-4b8b51180eb6

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
    @skip_if_bug_open('bugzilla', 1328202)
    def test_positive_delete_by_id(self):
        """Check if content host can be created and deleted by passing its ID

        @id: 1aa55e52-a97e-4c11-aab1-244bd4de0dd3

        @Assert: Content host is created and then deleted

        @BZ: 1328202
        """
        for name in valid_hosts_list():
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

        @id: 22f1206c-b712-45e9-8e65-3a0a225d6188

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
    def test_positive_create_with_same_name(self):
        """Registering the same content host generates a new UUID.

        @id: 178d3570-7177-435b-96e9-bcbb6b0b63b3

        @Assert: The UUID generated is different when registering the same
        content host.
        """
        name = gen_string('alpha', 15).lower()
        content_host = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': name,
            u'organization-id': self.NEW_ORG['id'],
        })
        self.assertEqual(content_host['name'], name)
        result = make_content_host({
            u'content-view-id': self.DEFAULT_CV['id'],
            u'lifecycle-environment-id': self.LIBRARY['id'],
            u'name': name,
            u'organization-id': self.NEW_ORG['id'],
        })
        self.assertEqual(result['name'], name)
        self.assertEqual(result['lifecycle-environment'], self.LIBRARY['name'])
        self.assertEqual(result['content-view'], self.DEFAULT_CV['name'])
        self.assertNotEqual(result['id'], content_host['id'])

    @tier3
    def test_positive_register_with_no_ak(self):
        """Register Content host to satellite without activation key

        @id: 6a7cedd2-aa9c-4113-a83b-3f0eea43ecb4

        @Assert: Content host successfully registered to appropriate org

        @CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            result = client.run(
                u'subscription-manager register --org {0} '
                '--environment {1}/{2} --username {3} --password {4}'
                .format(
                    self.NEW_ORG['label'],
                    self.NEW_LIFECYCLE['label'],
                    self.PROMOTED_CV['label'],
                    self.foreman_user,
                    self.foreman_password
                )
            )
            self.assertEqual(result.return_code, 0)

    @tier3
    def test_negative_register_twice(self):
        """Attempt to register a Content host twice to Satellite

        @id: 0af81129-cd69-4fa7-a128-9e8fcf2d03b1

        @Assert: Content host cannot be registered twice

        @CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.NEW_ORG['label'],
                activation_key['name'],
            )
            result = client.register_contenthost(
                self.NEW_ORG['label'],
                activation_key['name'],
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

        @id: b9c056cd-11ca-4870-bac4-0ebc4a782cb0

        @Assert: Content hosts are listed for the given org

        @CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.NEW_ORG['label'],
                activation_key['name'],
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

        @id: c5ce988d-d0ea-4958-9956-5a4b039b285c

        @Assert: After unregistering, content hosts list for the org does not
        show the content host

        @CaseLevel: System
        """
        activation_key = make_activation_key({
            'content-view-id': self.PROMOTED_CV['id'],
            'lifecycle-environment-id': self.NEW_LIFECYCLE['id'],
            'organization-id': self.NEW_ORG['id'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(
                self.NEW_ORG['label'],
                activation_key['name'],
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
