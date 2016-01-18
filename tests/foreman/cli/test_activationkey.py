# -*- encoding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg
"""Test class for Activation key CLI"""

from fauxfactory import gen_string
from robottelo import manifests
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_view,
    make_host_collection,
    make_lifecycle_environment,
    make_org,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription
from robottelo.constants import FAKE_0_YUM_REPO, PRDS, REPOS, REPOSET
from robottelo.datafactory import valid_data_list, invalid_values_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


class ActivationKeyTestCase(CLITestCase):
    """Activation Key CLI tests"""

    @classmethod
    def setUpClass(cls):
        """Tests for activation keys via Hammer CLI"""
        super(ActivationKeyTestCase, cls).setUpClass()
        cls.org = make_org()

    @staticmethod
    def get_default_env():
        """Get default lifecycle environment"""
        return LifecycleEnvironment.info({
            'organization-id': ActivationKeyTestCase.org['id'],
            'name': 'Library',
        })

    def _make_activation_key(self, options=None):
        """Make a new activation key and assert its success"""
        if options is None:
            options = {}

        # Use default organization if None are provided
        if (not options.get('organization', None) and
                not options.get('organization-label', None) and
                not options.get('organization-id', None)):
            options['organization-id'] = self.org['id']

        # Create activation key
        return make_activation_key(options)

    @tier1
    def test_positive_create_with_name(self):
        """Create Activation key for all variations of Activation key
        name

        @Feature: Activation key

        @Assert: Activation key is created with chosen name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_ak = self._make_activation_key({u'name': name})
                self.assertEqual(new_ak['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """Create Activation key for all variations of Description

        @Feature: Activation key

        @Assert: Activation key is created with chosen description
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_ak = self._make_activation_key({
                    u'description': desc,
                })
                self.assertEqual(new_ak['description'], desc)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_default_lce_by_id(self):
        """Create Activation key with associated default environment

        @Feature: Activation key

        @Assert: Activation key is created and associated to Library
        """
        lce = self.get_default_env()
        new_ak_env = self._make_activation_key({
            u'lifecycle-environment-id': lce['id'],
        })
        self.assertEqual(new_ak_env['lifecycle-environment'], lce['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_non_default_lce(self):
        """Create Activation key with associated custom environment

        @Feature: Activation key

        @Assert: Activation key is created and associated to expected
        environment
        """
        env = make_lifecycle_environment({u'organization-id': self.org['id']})
        new_ak_env = self._make_activation_key({
            u'lifecycle-environment-id': env['id'],
        })
        self.assertEqual(new_ak_env['lifecycle-environment'], env['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_default_lce_by_name(self):
        """Create Activation key with associated environment by name

        @feature: Activation key - Positive Create

        @assert: Activation key is created
        """
        lce = self.get_default_env()
        new_ak_env = self._make_activation_key({
            u'lifecycle-environment': lce['name'],
        })
        self.assertEqual(new_ak_env['lifecycle-environment'], lce['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_cv(self):
        """Create Activation key for all variations of Content Views

        @Feature: Activation key - Positive Create

        @Assert: Activation key is created and has proper content view assigned
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_cv = make_content_view({
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                new_ak_cv = self._make_activation_key({
                    u'content-view': new_cv['name'],
                    u'environment': self.get_default_env()['name'],
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(new_ak_cv['content-view'], name)

    @tier1
    def test_positive_create_with_usage_limit_default(self):
        """Create Activation key with default Usage limit (Unlimited)

        @Feature: Activation key - Positive Create

        @Assert: Activation key is created
        """
        new_ak = self._make_activation_key()
        self.assertEqual(new_ak['content-host-limit'], u'Unlimited')

    @tier1
    def test_positive_create_with_usage_limit_default_explicitly(self):
        """Create Activation key with default Usage limit (Unlimited)

        @Feature: Activation key - Positive Create

        @Assert: Activation key is created
        """
        new_ak = self._make_activation_key({u'unlimited-content-hosts': '1'})
        self.assertEqual(new_ak['content-host-limit'], u'Unlimited')

    @tier1
    def test_positive_create_with_usage_limit_finite(self):
        """Create Activation key with finite Usage limit

        @Feature: Activation key - Positive Create

        @Assert: Activation key is created
        """
        new_ak = self._make_activation_key({
            u'unlimited-content-hosts': '0',
            u'max-content-hosts': '10',
        })
        self.assertEqual(new_ak['content-host-limit'], u'10')

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Activation key with invalid Name

        @Feature: Activation key - Negative Create

        @Assert: Activation key is not created. Appropriate error shown.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_activation_key({u'name': name})

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1177158)
    @tier1
    def test_negative_create_with_invalid_description(self):
        """Create Activation key with invalid Description

        @Feature: Activation key - Negative Create

        @BZ: 1177158

        @Assert: Activation key is not created. Appropriate error shown.
        """
        with self.assertRaises(CLIFactoryError):
            self._make_activation_key(
                {u'description': gen_string('alpha', 1001)})

    @tier1
    def test_negative_create_with_usage_limit(self):
        """Create Activation key with invalid Usage Limit

        @Feature: Activation key - Negative Create

        @Assert: Activation key is not created. Appropriate error shown.
        """
        include_list = ['-1', '-500', 0, 0.5]
        for limit in invalid_values_list() + include_list:
            with self.subTest(limit):
                with self.assertRaises(CLIFactoryError):
                    self._make_activation_key({
                        u'unlimited-content-hosts': '0',
                        u'max-content-hosts': limit,
                    })

    @tier1
    def test_positive_delete_by_name(self):
        """Create Activation key and delete it for all variations of
        Activation key name

        @Feature: Activation key - Positive Delete

        @Assert: Activation key is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_ak = self._make_activation_key({
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                ActivationKey.delete({
                    'name': new_ak['name'],
                    'organization-id': self.org['id'],
                })
                with self.assertRaises(CLIReturnCodeError):
                    ActivationKey.info({'id': new_ak['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_org_name(self):
        """Create Activation key and delete it using organization name
        for which that key was created

        @Feature: Activation key - Positive Delete

        @Assert: Activation key is deleted
        """
        new_ak = self._make_activation_key()
        ActivationKey.delete({
            'name': new_ak['name'],
            'organization': self.org['name'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': new_ak['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_org_label(self):
        """Create Activation key and delete it using organization label
        for which that key was created

        @Feature: Activation key - Positive Delete

        @Assert: Activation key is deleted
        """
        new_ak = self._make_activation_key()
        ActivationKey.delete({
            'name': new_ak['name'],
            'organization-label': self.org['label'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': new_ak['id']})

    @run_only_on('sat')
    @tier2
    def test_positive_delete_with_cv(self):
        """Create activation key with content view assigned to it and
        delete it using activation key id

        @Feature: Activation key - Positive Delete

        @Assert: Activation key is deleted
        """
        new_cv = make_content_view({u'organization-id': self.org['id']})
        new_ak = self._make_activation_key({u'content-view': new_cv['name']})
        ActivationKey.delete({'id': new_ak['id']})
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': new_ak['id']})

    @run_only_on('sat')
    @tier2
    def test_positive_delete_with_lce(self):
        """Create activation key with lifecycle environment assigned to
        it and delete it using activation key id

        @Feature: Activation key - Positive Delete

        @Assert: Activation key is deleted
        """
        new_ak = self._make_activation_key({
            u'lifecycle-environment': self.get_default_env()['name'],
        })
        ActivationKey.delete({'id': new_ak['id']})
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': new_ak['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_by_id(self):
        """Update Activation Key Name in Activation key searching by ID

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        activation_key = self._make_activation_key()
        for name in valid_data_list():
            with self.subTest(name):
                ActivationKey.update({
                    u'id': activation_key['id'],
                    u'new-name': name,
                    u'organization-id': self.org['id'],
                })
                updated_ak = ActivationKey.info({'id': activation_key['id']})
                self.assertEqual(updated_ak['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_by_name(self):
        """Update Activation Key Name in an Activation key searching by
        name

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        new_name = gen_string('alpha')
        activation_key = self._make_activation_key()
        ActivationKey.update({
            u'name': activation_key['name'],
            u'new-name': new_name,
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': activation_key['id']})
        self.assertEqual(updated_ak['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Update Description in an Activation key

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        activation_key = self._make_activation_key()
        for description in valid_data_list():
            with self.subTest(description):
                ActivationKey.update({
                    u'description': description,
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                updated_ak = ActivationKey.info({'id': activation_key['id']})
                self.assertEqual(updated_ak['description'], description)

    @run_only_on('sat')
    @tier2
    def test_positive_update_lce(self):
        """Update Environment in an Activation key

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        ak_env = self._make_activation_key({
            u'lifecycle-environment-id': self.get_default_env()['id'],
        })
        env = make_lifecycle_environment({u'organization-id': self.org['id']})
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': new_cv['id']})
        cvv = ContentView.info({u'id': new_cv['id']})['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        ActivationKey.update({
            u'id': ak_env['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view': new_cv['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': ak_env['id']})
        self.assertEqual(updated_ak['lifecycle-environment'], env['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_update_cv(self):
        """Update Content View in an Activation key

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        ak_cv = self._make_activation_key({u'content-view-id': cv['id']})
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ActivationKey.update({
            u'content-view': new_cv['name'],
            u'name': ak_cv['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': ak_cv['id']})
        self.assertEqual(updated_ak['content-view'], new_cv['name'])

    @tier1
    def test_positive_update_usage_limit_to_finite_number(self):
        """Update Usage limit from Unlimited to a finite number

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        new_ak = self._make_activation_key()
        self.assertEqual(new_ak['content-host-limit'], u'Unlimited')
        ActivationKey.update({
            u'unlimited-content-hosts': '0',
            u'max-content-hosts': '2147483647',
            u'name': new_ak['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': new_ak['id']})
        self.assertEqual(updated_ak['content-host-limit'], u'2147483647')

    @tier1
    def test_positive_update_usage_limit_to_unlimited(self):
        """Update Usage limit from definite number to Unlimited

        @Feature: Activation key - Positive Update

        @Assert: Activation key is updated
        """
        new_ak = self._make_activation_key({
            u'unlimited-content-hosts': '0',
            u'max-content-hosts': '10',
        })
        self.assertEqual(new_ak['content-host-limit'], u'10')
        ActivationKey.update({
            u'unlimited-content-hosts': '1',
            u'name': new_ak['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': new_ak['id']})
        self.assertEqual(updated_ak['content-host-limit'], u'Unlimited')

    @tier1
    def test_negative_update_name(self):
        """Try to update Activation Key using invalid value for its name

        @Feature: Activation key - Negative Update

        @Assert: Activation key is not updated. Appropriate error shown.
        """
        new_ak = self._make_activation_key()
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    ActivationKey.update({
                        u'id': new_ak['id'],
                        u'new-name': name,
                        u'organization-id': self.org['id'],
                    })

    @skip_if_bug_open('bugzilla', 1177158)
    @tier1
    def test_negative_update_description(self):
        """Try to update Activation Key using invalid value for its
        description

        @Feature: Activation key - Negative Update

        @BZ: 1177158

        @Assert: Activation key is not updated. Appropriate error shown.
        """
        new_ak = self._make_activation_key()
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.update({
                u'id': new_ak['id'],
                u'description': gen_string('alpha', 1001),
                u'organization-id': self.org['id'],
            })

    @tier1
    def test_negative_update_usage_limit(self):
        """Try to update Activation Key using invalid value for its
        usage limit attribute

        @Feature: Activation key - Negative Update

        @Assert: Activation key is not updated. Appropriate error shown.
        """
        new_ak = self._make_activation_key()
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.update({
                u'unlimited-content-hosts': '0',
                u'max-content-hosts': int('9' * 20),
                u'id': new_ak['id'],
                u'organization-id': self.org['id'],
            })

    @skip_if_not_set('clients')
    @tier3
    def test_positive_usage_limit(self):
        """Test that Usage limit actually limits usage

        @Feature: Activation key - Usage limit

        @Steps:

        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Content hosts to match the Usage Limit
        4. Attempt to register an other Content host after reaching the Usage
           Limit

        @Assert: Content host Registration fails. Appropriate error shown
        """
        env = make_lifecycle_environment({u'organization-id': self.org['id']})
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': new_cv['id']})
        cvv = ContentView.info({u'id': new_cv['id']})['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        new_ak = make_activation_key({
            u'lifecycle-environment-id': env['id'],
            u'content-view': new_cv['name'],
            u'organization-id': self.org['id'],
            u'unlimited-content-hosts': '0',
            u'max-content-hosts': '1',
        })
        with VirtualMachine(distro='rhel65') as vm1:
            with VirtualMachine(distro='rhel65') as vm2:
                vm1.install_katello_ca()
                result = vm1.register_contenthost(
                    new_ak['name'], self.org['label'])
                self.assertEqual(result.return_code, 0)
                vm2.install_katello_ca()
                result = vm2.register_contenthost(
                    new_ak['name'], self.org['label'])
                self.assertEqual(result.return_code, 255)
                self.assertGreater(len(result.stderr), 0)

    @skip_if_bug_open('bugzilla', 1110476)
    @tier2
    def test_positive_update_host_collection(self):
        """Test that host collection can be associated to Activation
        Keys

        @Feature: Activation key - Host

        @BZ: 1110476

        @Assert: Hosts are successfully associated to Activation key
        """
        for host_col_name in valid_data_list():
            with self.subTest(host_col_name):
                activation_key = self._make_activation_key()
                new_host_col_name = make_host_collection({
                    'name': host_col_name,
                })['name']
                # Assert that name matches data passed
                self.assertEqual(new_host_col_name, host_col_name)
                ActivationKey.add_host_collection({
                    u'host-collection': new_host_col_name,
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    u'id': activation_key['id'],
                })
                self.assertEqual(
                    activation_key['host-collection'], host_col_name)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1293585)
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_add_redhat_product(self):
        """Test that RH product can be associated to Activation Keys

        @Feature: Activation key - Product

        @BZ: 1293585

        @Assert: RH products are successfully associated to Activation key
        """
        result = setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': self.org['id'],
        })
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(content[0]['name'], REPOSET['rhst7'])

    @run_only_on('sat')
    @tier3
    def test_positive_add_custom_product(self):
        """Test that custom product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Assert: Custom products are successfully associated to Activation key
        """
        result = setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': self.org['id'],
        })
        repo = Repository.info({u'id': result['repository-id']})
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(content[0]['name'], repo['name'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1293585)
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_add_redhat_and_custom_products(self):
        """Test if RH/Custom product can be associated to Activation key

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @BZ: 1293585

        @Assert: RH/Custom product is successfully associated to Activation key
        """
        result = setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': self.org['id'],
        })
        result = setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': self.org['id'],
            u'activationkey-id': result['activationkey-id'],
            u'content-view-id': result['content-view-id'],
            u'lifecycle-environment-id': result['lifecycle-environment-id'],
        })
        repo = Repository.info({u'id': result['repository-id']})
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['name'], REPOSET['rhst7'])
        self.assertEqual(content[1]['name'], repo['name'])

    @stubbed()
    def test_positive_delete_manifest(self):
        """Check if deleting a manifest removes it from Activation key

        @Feature: Activation key - Manifest

        @Steps:
        1. Upload manifest
        2. Create activation key - attach some subscriptions
        3. Delete manifest
        4. See if the activation key automatically removed the subscriptions.

        @Assert: Deleting a manifest removes it from the Activation key

        @Status: Manual
        """

    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_delete_subscription(self):
        """Check if deleting a subscription removes it from Activation key

        @Feature: Activation key - Subscription

        @Assert: Deleting subscription removes it from the Activation key
        """
        new_ak = self._make_activation_key()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': self.org['id'],
        })
        subscription_result = Subscription.list({
            'organization-id': self.org['id'],
            'order': 'id desc'
        }, per_page=False)
        result = ActivationKey.add_subscription({
            u'id': new_ak['id'],
            u'subscription-id': subscription_result[-1]['id'],
        })
        self.assertIn('Subscription added to activation key', result)
        ak_subs_info = ActivationKey.subscriptions({
            u'id': new_ak['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(len(ak_subs_info), 6)
        result = ActivationKey.remove_subscription({
            u'id': new_ak['id'],
            u'subscription-id': subscription_result[-1]['id'],
        })
        self.assertIn('Subscription removed from activation key', result)
        ak_subs_info = ActivationKey.subscriptions({
            u'id': new_ak['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(len(ak_subs_info), 4)

    @skip_if_not_set('clients')
    @tier3
    def test_positive_update_aks_to_chost(self):
        """Check if multiple Activation keys can be attached to a
        Content host

        @Feature: Activation key - Content host

        @Assert: Multiple Activation keys are attached to a Content host
        """
        env = make_lifecycle_environment({u'organization-id': self.org['id']})
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': new_cv['id']})
        cvv = ContentView.info({u'id': new_cv['id']})['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        new_aks = [
            make_activation_key({
                u'lifecycle-environment-id': env['id'],
                u'content-view': new_cv['name'],
                u'organization-id': self.org['id'],
            })
            for _ in range(2)
        ]
        with VirtualMachine(distro='rhel65') as vm:
            vm.install_katello_ca()
            for i in range(2):
                result = vm.register_contenthost(
                    new_aks[i]['name'], self.org['label'])
                self.assertEqual(result.return_code, 0)

    @skip_if_not_set('clients')
    @stubbed()
    @tier3
    def test_positive_update_aks_to_chost_in_one_command(self):
        """Check if multiple Activation keys can be attached to a
        Content host in one command. Here is a command details

        subscription-manager register --help

        ...

        --activationkey=ACTIVATION_KEYS activation key to use for registration
        (can be specified more than once)

        ...

        This means that we can re-use `--activationkey` option more than once
        to add different keys

        @Feature: Activation key - Content host

        @Assert: Multiple Activation keys are attached to a Content host
        """

    @tier1
    def test_positive_list_by_name(self):
        """List Activation key for all variations of Activation key name

        @Feature: Activation key - list

        @Assert: Activation key is listed
        """
        for name in valid_data_list():
            with self.subTest(name):
                self._make_activation_key({u'name': name})
                result = ActivationKey.list({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], name)

    @tier1
    def test_positive_list_by_cv_id(self):
        """List Activation key for provided Content View ID

        @Feature: Activation key - list

        @Assert: Activation key is listed
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        self._make_activation_key({u'content-view-id': cv['id']})
        result = ActivationKey.list({
            'content-view-id': cv['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['content-view'], cv['name'])

    @tier1
    def test_positive_create_using_old_name(self):
        """Create activation key, rename it and create another with the
        initial name

        @Feature: Activation key - Positive Create

        @Assert: Activation key is created
        """
        name = gen_string('utf8')
        activation_key = self._make_activation_key({'name': name})
        new_name = gen_string('utf8')
        ActivationKey.update({
            u'id': activation_key['id'],
            u'new-name': new_name,
            u'organization-id': self.org['id'],
        })
        activation_key = ActivationKey.info({'id': activation_key['id']})
        self.assertEqual(activation_key['name'], new_name)
        new_activation_key = self._make_activation_key({
            u'name': name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(new_activation_key['name'], name)

    @tier2
    def test_positive_remove_host_collection_by_id(self):
        """Test that hosts associated to Activation Keys can be removed
        using id of that host collection

        @Feature: Activation key - Host

        @Steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove host collection associated to Activation key using id of that
           collection

        @Assert: Host collection successfully removed from activation key
        """
        activation_key = self._make_activation_key()
        new_host_col = make_host_collection({
            u'name': gen_string('alpha'),
            u'organization-id': self.org['id'],
        })
        ActivationKey.add_host_collection({
            u'host-collection-id': new_host_col['id'],
            u'name': activation_key['name'],
            u'organization': self.org['name'],
        })
        activation_key = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(len(activation_key['host-collections']), 1)
        ActivationKey.remove_host_collection({
            u'host-collection-id': new_host_col['id'],
            u'name': activation_key['name'],
            u'organization': self.org['name'],
        })
        activation_key = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(len(activation_key['host-collections']), 0)

    @tier2
    def test_positive_remove_host_collection_by_name(self):
        """Test that hosts associated to Activation Keys can be removed
        using name of that host collection

        @Feature: Activation key - Host

        @Steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove the host collection associated to Activation key using name
           of that collection

        @Assert: Host collection successfully removed from activation key
        """
        for host_col in valid_data_list():
            with self.subTest(host_col):
                activation_key = self._make_activation_key()
                new_host_col = make_host_collection({
                    u'name': host_col,
                    u'organization-id': self.org['id'],
                })
                # Assert that name matches data passed
                self.assertEqual(new_host_col['name'], host_col)
                ActivationKey.add_host_collection({
                    u'host-collection': new_host_col['name'],
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    'id': activation_key['id'],
                })
                self.assertEqual(len(activation_key['host-collections']), 1)
                self.assertEqual(
                    activation_key['host-collections'][0]['name'],
                    host_col,
                )
                ActivationKey.remove_host_collection({
                    u'host-collection': new_host_col['name'],
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    u'id': activation_key['id'],
                })
                self.assertEqual(len(activation_key['host-collections']), 0)

    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_subscription_by_id(self):
        """Test that subscription can be added to activation key

        @Feature: Activation key - Subscription

        @Steps:

        1. Create Activation key
        2. Upload manifest and add subscription
        3. Associate the activation key to subscription

        @Assert: Subscription successfully added to activation key
        """
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        org_id = make_org()['id']
        ackey_id = self._make_activation_key()['id']
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org_id,
        })
        subs_id = Subscription.list(
            {'organization-id': org_id},
            per_page=False
        )
        result = ActivationKey.add_subscription({
            u'id': ackey_id,
            u'subscription-id': subs_id[0]['id'],
        })
        self.assertIn('Subscription added to activation key', result)

    @tier1
    def test_positive_copy_by_parent_id(self):
        """Copy Activation key for all valid Activation Key name
        variations

        @Feature: Activation key copy

        @Assert: Activation key is successfully copied
        """
        parent_ak = self._make_activation_key()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                result = ActivationKey.copy({
                    u'id': parent_ak['id'],
                    u'new-name': new_name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(result[0], u'Activation key copied')

    @tier1
    def test_positive_copy_by_parent_name(self):
        """Copy Activation key by passing name of parent

        @Feature: Activation key copy

        @Assert: Activation key is successfully copied
        """
        parent_ak = self._make_activation_key()
        result = ActivationKey.copy({
            u'name': parent_ak['name'],
            u'new-name': gen_string('alpha'),
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result[0], u'Activation key copied')

    @tier1
    def test_negative_copy_with_same_name(self):
        """Copy activation key with duplicate name

        @Feature: Activation key copy

        @Assert: Activation key is not successfully copied
        """
        parent_ak = self._make_activation_key()
        with self.assertRaises(CLIReturnCodeError) as exception:
            ActivationKey.copy({
                u'name': parent_ak['name'],
                u'new-name': parent_ak['name'],
                u'organization-id': self.org['id'],
            })
        self.assertEqual(exception.exception.return_code, 65)

    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_copy_subscription(self):
        """Copy Activation key and verify contents

        @Feature: Activation key copy

        @Steps:

        1. Create parent key and add content
        2. Copy Activation key by passing id of parent
        3. Verify content was successfully copied

        @Assert: Activation key is successfully copied
        """
        # Begin test setup
        parent_ak = self._make_activation_key()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': self.org['id'],
        })
        subscription_result = Subscription.list(
            {'organization-id': self.org['id']}, per_page=False)
        ActivationKey.add_subscription({
            u'id': parent_ak['id'],
            u'subscription-id': subscription_result[0]['id'],
        })
        # End test setup
        new_name = gen_string('utf8')
        result = ActivationKey.copy({
            u'id': parent_ak['id'],
            u'new-name': new_name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result[0], u'Activation key copied')
        result = ActivationKey.subscriptions({
            u'name': new_name,
            u'organization-id': self.org['id'],
        })
        # Verify that the subscription copied over
        self.assertIn(
            subscription_result[0]['name'],  # subscription name
            result[3]  # subscription list
        )

    @tier1
    def test_positive_update_autoattach_toggle(self):
        """Update Activation key with inverse auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Get the key's current auto attach value.
        2. Update the key with the value's inverse.
        3. Verify key was updated.

        @Assert: Activation key is successfully copied
        """
        new_ak = self._make_activation_key()
        attach_value = new_ak['auto-attach']
        # invert value
        new_value = u'false' if attach_value == u'true' else u'true'
        ActivationKey.update({
            u'auto-attach': new_value,
            u'id': new_ak['id'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': new_ak['id']})
        self.assertEqual(updated_ak['auto-attach'], new_value)

    @tier1
    def test_positive_update_autoattach(self):
        """Update Activation key with valid auto-attach values

        @Feature: Activation key update / info

        @Assert: Activation key is successfully updated
        """
        new_ak = self._make_activation_key()
        for new_value in (u'1', u'0', u'true', u'false', u'yes', u'no'):
            with self.subTest(new_value):
                result = ActivationKey.update({
                    u'auto-attach': new_value,
                    u'id': new_ak['id'],
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(
                    u'Activation key updated', result[0]['message'])

    @tier1
    def test_negative_update_autoattach(self):
        """Attempt to update Activation key with bad auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Attempt to update a key with incorrect auto-attach value
        2. Verify that an appropriate error message was returned

        @Assert: Activation key is not updated. Appropriate error shown.
        """
        new_ak = self._make_activation_key()
        with self.assertRaises(CLIReturnCodeError) as exe:
            ActivationKey.update({
                u'auto-attach': gen_string('utf8'),
                u'id': new_ak['id'],
                u'organization-id': self.org['id'],
            })
        self.assertIn(
            u"'--auto-attach': value must be one of", exe.exception.stderr)

    @skip_if_bug_open('bugzilla', 1180282)
    @tier3
    def test_positive_content_override(self):
        """Positive content override

        @Feature: Activation key copy

        @Steps:

        1. Create activation key and add content
        2. Get the first product's label
        3. Override the product's content enabled state
        4. Verify that the command succeeded

        @BZ: 1180282

        @Assert: Activation key content override was successful
        """
        result = setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': self.org['id'],
        })
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': self.org['id'],
        })
        for override_value in (u'1', u'0'):
            with self.subTest(override_value):
                ActivationKey.content_override({
                    u'content-label': content[0]['label'],
                    u'id': result['activationkey-id'],
                    u'organization-id': self.org['id'],
                    u'value': override_value,
                })
                # Retrieve the product content enabled flag
                content = ActivationKey.product_content({
                    u'id': result['activationkey-id'],
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(content[0]['enabled?'], override_value)
