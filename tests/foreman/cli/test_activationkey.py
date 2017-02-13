# -*- encoding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg
"""Test class for Activation key CLI

@Requirement: Activationkey

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

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
    make_user,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.constants import FAKE_0_YUM_REPO, PRDS, REPOS, REPOSET
from robottelo.constants import DISTRO_RHEL6
from robottelo.datafactory import valid_data_list, invalid_values_list
from robottelo.decorators import (
    run_in_one_thread,
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

        @id: a5aaab5e-bc18-459e-a384-74aef752ec88

        @Assert: Activation key is created with chosen name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_ak = self._make_activation_key({u'name': name})
                self.assertEqual(new_ak['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """Create Activation key for all variations of Description

        @id: 5a5ca7f9-1449-4365-ac8a-978605620bf2

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

        @id: 9171adb2-c9ac-4cda-978f-776826668aa3

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

        @id: ad4d4611-3fb5-4449-ae47-305f9931350e

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

        @id: 7410f7c4-e8b5-4080-b6d2-65dbcedffe8a

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

        @id: ec7b1af5-c3f4-40c3-b1df-c69c02a3b9a7

        @Assert: Activation key is created and has proper content view assigned

        @CaseLevel: Integration
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

        @id: cba13c72-9845-486d-beff-e0fb55bb762c

        @Assert: Activation key is created
        """
        new_ak = self._make_activation_key()
        self.assertEqual(new_ak['host-limit'], u'Unlimited')

    @tier1
    def test_positive_create_with_usage_limit_finite(self):
        """Create Activation key with finite Usage limit

        @id: 529a0f9e-977f-4e9d-a1af-88bb98c28a6a

        @Assert: Activation key is created
        """
        new_ak = self._make_activation_key({
            u'max-hosts': '10',
        })
        self.assertEqual(new_ak['host-limit'], u'10')

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Activation key with invalid Name

        @id: d9b7e3a9-1d24-4e47-bd4a-dce75772d829

        @Assert: Activation key is not created. Appropriate error shown.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_activation_key({u'name': name})

    @tier1
    def test_negative_create_with_usage_limit(self):
        """Create Activation key with invalid Usage Limit

        @id: 247ebc2e-c80f-488b-aeaf-6bf5eba55375

        @Assert: Activation key is not created. Appropriate error shown.
        """
        include_list = ['-1', '-500', 0, 0.5]
        for limit in invalid_values_list() + include_list:
            with self.subTest(limit):
                with self.assertRaises(CLIFactoryError):
                    self._make_activation_key({
                        u'max-hosts': limit,
                    })

    @tier1
    def test_positive_delete_by_name(self):
        """Create Activation key and delete it for all variations of
        Activation key name

        @id: ef5f6a28-6bfd-415b-aac9-b3dc9a014ca9

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

        @id: 006cbe5c-fb72-43a1-9760-30c97043c36b

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

        @id: f66e5a42-b531-4290-a907-9f5c01305885

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

        @id: bba323fa-0362-4a9b-97af-560d446cbb6c

        @Assert: Activation key is deleted

        @CaseLevel: Integration
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

        @id: e1830e52-5b1a-4ac4-8d0a-df6efb218a8b

        @Assert: Activation key is deleted

        @CaseLevel: Integration
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

        @id: bc304894-fd9b-4622-96e3-57c2257e26ca

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

        @id: bce4533e-1a58-4edb-a51a-4aa46bc28676

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

        @id: 60a4e860-d99c-431e-b70b-9b0fa90d839b

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

        @id: 55aaee60-b8c8-49f0-995a-6c526b9b653b

        @Assert: Activation key is updated

        @CaseLevel: Integration
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

        @id: aa94997d-fc9b-4532-aeeb-9f27b9834914

        @Assert: Activation key is updated

        @CaseLevel: Integration
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

        @id: a55bb8dc-c7d8-4a6a-ac0f-1d5a377da543

        @Assert: Activation key is updated
        """
        new_ak = self._make_activation_key()
        self.assertEqual(new_ak['host-limit'], u'Unlimited')
        ActivationKey.update({
            u'max-hosts': '2147483647',
            u'name': new_ak['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': new_ak['id']})
        self.assertEqual(updated_ak['host-limit'], u'2147483647')

    @tier1
    def test_positive_update_usage_limit_to_unlimited(self):
        """Update Usage limit from definite number to Unlimited

        @id: 0b83657b-41d1-4fb2-9c23-c36011322b83

        @Assert: Activation key is updated
        """
        new_ak = self._make_activation_key({
            u'max-hosts': '10',
        })
        self.assertEqual(new_ak['host-limit'], u'10')
        ActivationKey.update({
            u'unlimited-hosts': True,
            u'name': new_ak['name'],
            u'organization-id': self.org['id'],
        })
        updated_ak = ActivationKey.info({'id': new_ak['id']})
        self.assertEqual(updated_ak['host-limit'], u'Unlimited')

    @tier1
    def test_negative_update_name(self):
        """Try to update Activation Key using invalid value for its name

        @id: b75e7c38-fde2-4110-ba65-4157319fc159

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

    @tier1
    def test_negative_update_usage_limit(self):
        """Try to update Activation Key using invalid value for its
        usage limit attribute

        @id: cb5fa263-924c-471f-9c57-9506117ca92d

        @Assert: Activation key is not updated. Appropriate error shown.
        """
        new_ak = self._make_activation_key()
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.update({
                u'max-hosts': int('9' * 20),
                u'id': new_ak['id'],
                u'organization-id': self.org['id'],
            })

    @skip_if_not_set('clients')
    @tier3
    def test_positive_usage_limit(self):
        """Test that Usage limit actually limits usage

        @id: 00ded856-e939-4140-ac84-91b6a8643623

        @Steps:

        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Content hosts to match the Usage Limit
        4. Attempt to register an other Content host after reaching the Usage
           Limit

        @Assert: Content host Registration fails. Appropriate error shown

        @CaseLevel: System
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
            u'max-hosts': '1',
        })
        with VirtualMachine(distro=DISTRO_RHEL6) as vm1:
            with VirtualMachine(distro=DISTRO_RHEL6) as vm2:
                vm1.install_katello_ca()
                result = vm1.register_contenthost(
                    self.org['label'], new_ak['name'])
                self.assertEqual(result.return_code, 0)
                vm2.install_katello_ca()
                result = vm2.register_contenthost(
                    self.org['label'], new_ak['name'])
                self.assertEqual(result.return_code, 255)
                self.assertGreater(len(result.stderr), 0)

    @skip_if_bug_open('bugzilla', 1110476)
    @tier2
    def test_positive_update_host_collection(self):
        """Test that host collection can be associated to Activation
        Keys

        @id: 2114132a-fede-4791-98e7-a463ad79f398

        @BZ: 1110476

        @Assert: Hosts are successfully associated to Activation key

        @CaseLevel: Integration
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

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_add_redhat_product(self):
        """Test that RH product can be associated to Activation Keys

        @id: 7b15de8e-edde-41aa-937b-ad6aa529891a

        @Assert: RH products are successfully associated to Activation key

        @CaseLevel: System
        """
        org = make_org()
        result = setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': org['id'],
        })
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': org['id'],
        })
        self.assertEqual(content[0]['name'], REPOSET['rhst7'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1360239)
    @tier3
    def test_positive_add_custom_product(self):
        """Test that custom product can be associated to Activation Keys

        @id: 96ace967-e165-4069-8ff7-f54c4c822de0

        @Assert: Custom products are successfully associated to Activation key

        @CaseLevel: System
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

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1360239)
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_add_redhat_and_custom_products(self):
        """Test if RH/Custom product can be associated to Activation key

        @id: 74c77426-18f5-4abb-bca9-a2135f7fcc1f

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @Assert: RH/Custom product is successfully associated to Activation key

        @CaseLevel: System
        """
        org = make_org()
        result = setup_org_for_a_rh_repo({
            u'product': PRDS['rhel'],
            u'repository-set': REPOSET['rhst7'],
            u'repository': REPOS['rhst7']['name'],
            u'organization-id': org['id'],
        })
        result = setup_org_for_a_custom_repo({
            u'url': FAKE_0_YUM_REPO,
            u'organization-id': org['id'],
            u'activationkey-id': result['activationkey-id'],
            u'content-view-id': result['content-view-id'],
            u'lifecycle-environment-id': result['lifecycle-environment-id'],
        })
        repo = Repository.info({u'id': result['repository-id']})
        content = ActivationKey.product_content({
            u'id': result['activationkey-id'],
            u'organization-id': org['id'],
        })
        self.assertEqual(len(content), 2)
        self.assertEqual(
            {REPOSET['rhst7'], repo['name']}, {pc['name'] for pc in content})

    @stubbed()
    def test_positive_delete_manifest(self):
        """Check if deleting a manifest removes it from Activation key

        @id: 8256ac6d-3f60-4668-897d-2e88d29532d3

        @Steps:
        1. Upload manifest
        2. Create activation key - attach some subscriptions
        3. Delete manifest
        4. See if the activation key automatically removed the subscriptions.

        @Assert: Deleting a manifest removes it from the Activation key

        @caseautomation: notautomated
        """

    @run_in_one_thread
    @skip_if_bug_open('bugzilla', 1339211)
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_delete_subscription(self):
        """Check if deleting a subscription removes it from Activation key

        @id: bbbe4641-bfb0-48d6-acfc-de4294b18c15

        @Assert: Deleting subscription removes it from the Activation key

        @CaseLevel: Integration
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

        @id: 24fddd9c-03ae-41a7-8649-72296cbbafdf

        @Assert: Multiple Activation keys are attached to a Content host

        @CaseLevel: System
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
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            vm.install_katello_ca()
            for i in range(2):
                result = vm.register_contenthost(
                    self.org['label'], new_aks[i]['name'])
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

        @id: 888669e2-2ff7-48e3-9c56-6ac497bec5a0

        @Assert: Multiple Activation keys are attached to a Content host

        @CaseLevel: System
        """

    @tier1
    def test_positive_list_by_name(self):
        """List Activation key for all variations of Activation key name

        @id: 644b70d9-86c1-4e26-b38e-6aafab3efa34

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

        @id: 4d9aad38-cd6e-41cb-99a0-9a593cf22655

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

        @id: 9801319a-f42c-41a4-9ea4-3718e544c8e0

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

    @skip_if_bug_open('bugzilla', 1336716)
    @tier2
    def test_positive_remove_host_collection_by_id(self):
        """Test that hosts associated to Activation Keys can be removed
        using id of that host collection

        @id: 20f8ecca-1756-4900-b966-f0144b6bd0aa

        @Steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove host collection associated to Activation key using id of that
           collection

        @Assert: Host collection successfully removed from activation key

        @CaseLevel: Integration
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

    @skip_if_bug_open('bugzilla', 1336716)
    @tier2
    def test_positive_remove_host_collection_by_name(self):
        """Test that hosts associated to Activation Keys can be removed
        using name of that host collection

        @id: 1a559a82-db5f-48b0-beeb-2fa02aed7ef9

        @Steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove the host collection associated to Activation key using name
           of that collection

        @Assert: Host collection successfully removed from activation key

        @CaseLevel: Integration
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

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_subscription_by_id(self):
        """Test that subscription can be added to activation key

        @id: b884be1c-b35d-440a-9a9d-c854c83e10a7

        @Steps:

        1. Create Activation key
        2. Upload manifest and add subscription
        3. Associate the activation key to subscription

        @Assert: Subscription successfully added to activation key

        @CaseLevel: Integration
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

        @id: c9ad8aff-07ba-4804-a198-f719fe905123

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

        @id: 5d5405e6-3b26-47a3-96ff-f6c0f6c32607

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

        @id: f867c468-4155-495c-a1e5-c04d9868a2e0

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

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_copy_subscription(self):
        """Copy Activation key and verify contents

        @id: f4ee8096-4120-4d06-8c9a-57ac1eaa8f68

        @Steps:

        1. Create parent key and add content
        2. Copy Activation key by passing id of parent
        3. Verify content was successfully copied

        @Assert: Activation key is successfully copied

        @CaseLevel: Integration
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

        @id: de3b5fb7-7963-420a-b4c9-c66e78a111dc

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

        @id: 9e18b950-6f0f-4f82-a3ac-ef6aba950a78

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

        @id: 54b6f808-ff54-4e69-a54d-e1f99a4652f9

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

    @skip_if_bug_open('bugzilla', 1360239)
    @tier3
    def test_positive_content_override(self):
        """Positive content override

        @id: a4912cc0-3bf7-4e90-bb51-ec88b2fad227

        @Steps:

        1. Create activation key and add content
        2. Get the first product's label
        3. Override the product's content enabled state
        4. Verify that the command succeeded

        @Assert: Activation key content override was successful

        @CaseLevel: System
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

    @tier2
    def test_positive_remove_user(self):
        """Delete any user who has previously created an activation key
        and check that activation key still exists

        @id: ba9c4b29-2349-47ea-8081-917de2c17ed2

        @Assert: Activation Key can be read

        @BZ: 1291271
        """
        password = gen_string('alpha')
        user = make_user({'password': password, 'admin': 'true'})
        ak = ActivationKey.with_user(
            username=user['login'],
            password=password
        ).create({
            'name': gen_string('alpha'),
            'organization-id': self.org['id'],
        })
        User.delete({'id': user['id']})
        try:
            ActivationKey.info({'id': ak['id']})
        except CLIReturnCodeError:
            self.fail("Activation Key can't be read")
