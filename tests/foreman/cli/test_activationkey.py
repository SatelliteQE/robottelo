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
    make_lifecycle_environment,
    make_org, make_product, make_repository,
    make_host_collection
)
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


class ActivationKeyTestCase(CLITestCase):
    """Activation Key CLI tests"""
    org = None
    library = None
    env1 = None
    pub_key = None

    def setUp(self):
        """Tests for activation keys via Hammer CLI"""
        super(ActivationKeyTestCase, self).setUp()
        if ActivationKeyTestCase.org is None:
            ActivationKeyTestCase.org = make_org(cached=True)

    @staticmethod
    def update_env():
        """Populate env1 and env2"""
        if ActivationKeyTestCase.env1 is None:
            ActivationKeyTestCase.env1 = make_lifecycle_environment(
                {u'organization-id': ActivationKeyTestCase.org['id']},
                cached=True)

    @staticmethod
    def update_library():
        """Populate library"""
        if ActivationKeyTestCase.library is None:
            ActivationKeyTestCase.library = LifecycleEnvironment.info(
                {'organization-id': ActivationKeyTestCase.org['id'],
                 'name': 'Library'})

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

    def _make_public_key(self):
        """Perform all the steps needed to populate an Activation Key"""
        if ActivationKeyTestCase.pub_key is None:
            ActivationKeyTestCase.pub_key = {}
            try:
                organization_id = make_org()['id']
                ActivationKeyTestCase.pub_key['org_id'] = organization_id
                ActivationKeyTestCase.pub_key['prod_id'] = make_product({
                    'organization-id': organization_id,
                })['id']
                ActivationKeyTestCase.pub_key['manifest'] = manifests.clone()

                upload_file(ActivationKeyTestCase.pub_key['manifest'])
                Subscription.upload({
                    'file': ActivationKeyTestCase.pub_key['manifest'],
                    'organization-id': ActivationKeyTestCase.pub_key['org_id'],
                })

                # create content view
                ActivationKeyTestCase.pub_key['content_view_id'] = (
                    make_content_view({
                        u'organization-id': (
                            ActivationKeyTestCase.pub_key['org_id']),
                        u'name': gen_string('alpha'),
                    })['id']
                )

                ActivationKeyTestCase.pub_key['repo_id'] = make_repository({
                    u'product-id': ActivationKeyTestCase.pub_key['prod_id'],
                })['id']

                Repository.synchronize({
                    'id': ActivationKeyTestCase.pub_key['repo_id'],
                    'organization-id': ActivationKeyTestCase.pub_key['org_id'],
                })

                ContentView.add_repository({
                    u'id': ActivationKeyTestCase.pub_key['content_view_id'],
                    u'repository-id': ActivationKeyTestCase.pub_key['repo_id'],
                })

                ContentView.publish({
                    u'id': ActivationKeyTestCase.pub_key['content_view_id'],
                })

                ActivationKeyTestCase.pub_key['key_id'] = make_activation_key({
                    u'organization-id': ActivationKeyTestCase.pub_key['org_id']
                })['id']

                subscription_result = Subscription.list({
                    'organization-id': ActivationKeyTestCase.pub_key['org_id'],
                    'order': 'id desc'
                }, per_page=False)

                ActivationKey.add_subscription({
                    u'id': ActivationKeyTestCase.pub_key['key_id'],
                    u'subscription-id': subscription_result[-1]['id'],
                })
            except CLIFactoryError as err:
                ActivationKeyTestCase.pub_key = None
                self.fail(err)

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create Activation key for all variations of Activation key
        name

        @Feature: Activation key

        @Steps:

        1. Create Activation key for all valid Activation Key name variation

        @Assert: Activation key is created with chosen name

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_ackey_name = self._make_activation_key({
                    u'name': name,
                })['name']
                # Name should match passed data
                self.assertEqual(new_ackey_name, name)

    @tier1
    def test_positive_create_with_description(self):
        """@Test: Create Activation key for all variations of Description

        @Feature: Activation key

        @Steps:

        1. Create Activation key for all valid Description variation

        @Assert: Activation key is created with chosen description

        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_ackey_description = self._make_activation_key({
                    u'description': desc,
                })['description']
                # Description should match passed data
                self.assertEqual(new_ackey_description, desc)

    @tier2
    def test_positive_create_with_lce_library(self):
        """@Test: Create Activation key and associate with Library environment

        @Feature: Activation key

        @Steps:

        1. Create Activation key for variations of Name / associated to Library

        @Assert: Activation key is created and associated to Library

        """
        self.update_library()
        for name in valid_data_list():
            with self.subTest(name):
                new_ackey_env = self._make_activation_key({
                    u'lifecycle-environment-id': self.library['id'],
                    u'name': name,
                })['lifecycle-environment']
                # Description should match passed data
                self.assertEqual(new_ackey_env, self.library['name'])

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_lce(self):
        """@Test: Create Activation key and associate with environment

        @Feature: Activation key

        @Steps:

        1. Create Activation key for variations of Name / associated to environ

        @Assert: Activation key is created and associated to environment

        """
        self.update_env()
        for name in valid_data_list():
            with self.subTest(name):
                new_ackey_env = self._make_activation_key({
                    u'lifecycle-environment-id': self.env1['id'],
                    u'name': name,
                })['lifecycle-environment']
                # Description should match passed data
                self.assertEqual(new_ackey_env, self.env1['name'])

    @tier2
    def test_positive_create_with_cv(self):
        """@Test: Create Activation key for all variations of Content Views

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit

        @Assert: Activation key is created

        """
        for name in valid_data_list():
            with self.subTest(name):
                # Using the same name for content view and Activation key
                con_view = make_content_view({
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                new_ackey = self._make_activation_key({
                    u'content-view': con_view['name'],
                    u'environment': self.library['name'],
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                # Name should match passed data
                self.assertEqual(new_ackey['name'], name)
                # ContentView should match passed data
                self.assertEqual(new_ackey['content-view'], name)

    @stubbed()
    def test_positive_create_with_host_collection(self):
        """@Test: Create Activation key for all variations of Host Collections

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key for all valid host collections in [1]
        using valid Name, Description, Environment, Content View, Usage limit

        @Assert: Activation key is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_with_usage_limit_default(self):
        """@Test: Create Activation key with default Usage limit (Unlimited)

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_with_usage_limit_finite(self):
        """@Test: Create Activation key with finite Usage limit

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @Status: Manual

        """

    @stubbed()
    def test_positive_create_with_minimal_parameters(self):
        """@Test: Create Activation key with minimal input parameters

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values

        @Assert: Activation key is created

        @Status: Manual

        """

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_lce_by_name(self):
        """@test: Create Activation key with environment name

        @feature: Activation key - Positive Create

        @steps:

        1. Create Activation key by entering its name, a content view and a
        environment name.

        @assert: Activation key is created

        """
        self.update_library()
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        self._make_activation_key({
            u'content-view': content_view['name'],
            u'environment': self.library['name'],
            u'organization-id': self.org['id'],
        })

    @stubbed()
    def test_negative_create_with_name(self):
        """@Test: Create Activation key with invalid Name

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Activation Key Names in [2]
        using valid Description, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_create_with_description(self):
        """@Test: Create Activation key with invalid Description

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Description in [2]
        using valid Name, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_create_with_usage_limit(self):
        """@Test: Create Activation key with invalid Usage Limit

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Usage Limit in [2]
        using valid Name, Description, Environment, Content View

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """

    @tier1
    def test_delete_ak_by_name(self):
        """@Test: Create Activation key and delete it for all variations of
        Activation key name

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key for all valid Activation Key names
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                activation_key = self._make_activation_key({
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                ActivationKey.delete({
                    'name': activation_key['name'],
                    'organization-id': self.org['id'],
                })
                with self.assertRaises(CLIReturnCodeError):
                    ActivationKey.info({'id': activation_key['id']})

    @tier1
    def test_delete_ak_by_org_name(self):
        """@Test: Create Activation key and delete it using organization name
        for which that key was created

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key
        2. Delete Activation key using organization name

        @Assert: Activation key is deleted

        """
        activation_key = self._make_activation_key({
            u'description': gen_string('alpha'),
            u'name': gen_string('alpha'),
        })
        ActivationKey.delete({
            'name': activation_key['name'],
            'organization': self.org['name'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': activation_key['id']})

    @tier1
    def test_delete_ak_by_org_label(self):
        """@Test: Create Activation key and delete it using organization
        label for which that key was created

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key
        2. Delete Activation key using organization label

        @Assert: Activation key is deleted

        """
        activation_key = self._make_activation_key({
            u'name': gen_string('alpha'),
        })
        ActivationKey.delete({
            'name': activation_key['name'],
            'organization-label': self.org['label'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': activation_key['id']})

    @tier2
    def test_delete_ak_with_cv(self):
        """@Test: Create activation key with content view assigned to it and
        delete it using activation key id

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key with content view assigned to it
        2. Delete Activation key using activation key id

        @Assert: Activation key is deleted

        """
        contentview = make_content_view({
            u'organization-id': self.org['id'],
        })
        activation_key = self._make_activation_key({
            u'content-view': contentview['name'],
            u'name': gen_string('alpha'),
        })
        ActivationKey.delete({'id': activation_key['id']})
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': activation_key['id']})

    @tier2
    def test_delete_ak_with_env(self):
        """@Test: Create activation key with lifecycle environment assigned to
        it and delete it using activation key id

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key with lifecycle environment assigned to it
        2. Delete Activation key using activation key id

        @Assert: Activation key is deleted

        """
        self.update_env()
        env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        activation_key = self._make_activation_key({
            u'lifecycle-environment': env['name'],
            u'name': gen_string('alpha'),
        })
        ActivationKey.delete({'id': activation_key['id']})
        with self.assertRaises(CLIReturnCodeError):
            ActivationKey.info({'id': activation_key['id']})

    @tier1
    def test_positive_update_name_by_id(self):
        """@Test: Update Activation Key Name in Activation key searching by ID

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        """
        for name in valid_data_list():
            with self.subTest(name):
                activation_key = self._make_activation_key()
                ActivationKey.update({
                    u'id': activation_key['id'],
                    u'new-name': name,
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    'id': activation_key['id'],
                })
                self.assertEqual(activation_key['name'], name)

    @tier1
    def test_positive_update_name_by_name(self):
        """@Test: Update Activation Key Name in an Activation key searching by
        name

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        """
        for name in valid_data_list():
            with self.subTest(name):
                activation_key = self._make_activation_key()
                ActivationKey.update({
                    u'name': activation_key['name'],
                    u'new-name': name,
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    'id': activation_key['id'],
                })
                self.assertEqual(activation_key['name'], name)

    @tier1
    def test_positive_update_description(self):
        """@Test: Update Description in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Description for all variations in [1]

        @Assert: Activation key is updated

        """
        for description in valid_data_list():
            with self.subTest(description):
                activation_key = self._make_activation_key()
                ActivationKey.update({
                    u'description': description,
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    'id': activation_key['id'],
                })
                self.assertEqual(activation_key['description'], description)

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_lce(self):
        """@Test: Update Environment in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Environment for all variations in [1]

        @Assert: Activation key is updated

        @Status: Manual

        """

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1109649)
    def test_positive_update_cv(self):
        """@Test: Update Content View in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Content View for all variations in [1] and include both
           RH and custom products

        @Assert: Activation key is updated

        """
        activation_key = self._make_activation_key()
        for content_view_name in valid_data_list():
            with self.subTest(content_view_name):
                con_view = make_content_view({
                    u'name': content_view_name,
                    u'organization-id': self.org['id'],
                })
                ActivationKey.update({
                    u'content-view': con_view['name'],
                    u'name': activation_key['name'],
                    u'organization-id': self.org['id'],
                })
                activation_key = ActivationKey.info({
                    'id': activation_key['id'],
                })
                self.assertEqual(
                    activation_key['content-view'], content_view_name)

    @stubbed()
    def test_positive_update_usage_limit_to_finite_number(self):
        """@Test: Update Usage limit from Unlimited to a finite number

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Usage limit from Unlimited to a definite number

        @Assert: Activation key is updated

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_usage_limit_to_unlimited(self):
        """@Test: Update Usage limit from definite number to Unlimited

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Usage limit from definite number to Unlimited

        @Assert: Activation key is updated

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_name(self):
        """@Test: Update invalid name in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_description(self):
        """@Test: Update invalid Description in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Description for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_negative_update_usage_limit(self):
        """@Test: Update invalid Usage Limit in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Usage Limit for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """

    @stubbed()
    def test_positive_usage_limit(self):
        """@Test: Test that Usage limit actually limits usage

        @Feature: Activation key - Usage limit

        @Steps:

        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Content hosts to match the Usage Limit
        4. Attempt to register an other Content host after reaching the Usage
        Limit

        @Assert: Content host Registration fails. Appropriate error shown

        @Status: Manual

        """

    @tier2
    @skip_if_bug_open('bugzilla', 1110476)
    def test_positive_update_host_collection(self):
        """@Test: Test that host collection can be associated to Activation
        Keys

        @Feature: Activation key - Host

        @Steps:

        1. Create Activation key
        2. Create host collection
        3. Associate the host collection to Activation key

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

    @stubbed()
    def test_positive_update_redhat_product(self):
        """@Test: Test that RH product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key

        @Assert: RH products are successfully associated to Activation key

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_custom_product(self):
        """@Test: Test that custom product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate custom product(s) to Activation Key

        @Assert: Custom products are successfully associated to Activation key

        @Status: Manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_redhat_and_custom_products(self):
        """@Test: Test if RH/Custom product can be associated to Activation key

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @Assert: RH/Custom product is successfully associated to Activation key

        @Status: Manual

        """

    @stubbed()
    def test_positive_delete_manifest(self):
        """@Test: Check if deleting a manifest removes it from Activation key

        @Feature: Activation key - Manifest

        @Steps:

        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest

        @Assert: Deleting a manifest removes it from the Activation key

        @Status: Manual

        """

    @stubbed()
    def test_positive_update_aks_to_chost(self):
        """@Test: Check if multiple Activation keys can be attached to a
        Content host

        @Feature: Activation key - Content host

        @Steps:

        1. Create multiple Activation keys
        2. Attach all the created Activation keys to a Content host

        @Assert: Multiple Activation keys are attached to a Content host

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_by_name(self):
        """@Test: List Activation key for all variations of Activation key name

        @Feature: Activation key - list

        @Steps:

        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. List Activation key

        @Assert: Activation key is listed

        @Status: Manual

        """

    @stubbed()
    def test_positive_list_by_description(self):
        """@Test: List Activation key for all variations of Description

        @Feature: Activation key - list

        @Steps:

        1. Create Activation key for all valid Description variation in [1]
        2. List Activation key

        @Assert: Activation key is listed

        @Status: Manual

        """

    @stubbed()
    def test_positive_info(self):
        """@Test: Get Activation key info for all variations of Activation key
        name

        @Feature: Activation key - info

        @Steps:

        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. Get info of the Activation key

        @Assert: Activation key info is displayed

        @Status: Manual

        """

    @tier1
    def test_positive_create_using_old_name(self):
        """@test: Create activation key, rename it and create another with the
        initial name

        @feature: Activation key - Positive Create

        @steps:

        1. Create an activation key
        2. Rename it
        3. Create another activation key with the same name from step 1

        @assert: Activation key is created

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
        """@Test: Test that hosts associated to Activation Keys can be removed
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
        """@Test: Test that hosts associated to Activation Keys can be removed
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

    @tier2
    def test_positive_add_subscription_by_id(self):
        """@Test: Test that subscription can be added to activation key

        @Feature: Activation key - Host

        @Steps:

        1. Create Activation key
        2. Upload manifest and add subscription
        3. Associate the activation key to subscription

        @Assert: Subscription successfully added to activation key

        """
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        org_id = make_org()['id']
        ackey_id = self._make_activation_key()['id']
        Subscription.upload({
            'file': manifest,
            'organization-id': org_id,
        })
        subs_id = Subscription.list(
            {'organization-id': org_id},
            per_page=False)
        result = ActivationKey.add_subscription({
            u'id': ackey_id,
            u'subscription-id': subs_id[0]['id'],
        })
        self.assertIn('Subscription added to activation key', result)

    @tier1
    def test_positive_copy_by_parent_id(self):
        """@Test: Copy Activation key for all valid Activation Key name
           variations

        @Feature: Activation key copy

        @Steps:

        1. Copy Activation key for all valid Activation Key name variations

        @Assert: Activation key is sucessfully copied

        """
        parent_id = make_activation_key(
            {u'organization-id': self.org['id']},
            cached=True,
        )['id']
        for new_name in valid_data_list():
            with self.subTest(new_name):
                result = ActivationKey.copy({
                    u'id': parent_id,
                    u'new-name': new_name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(result[0], u'Activation key copied')

    @tier1
    def test_positive_copy_by_parent_name(self):
        """@Test: Copy Activation key by passing name of parent

        @Feature: Activation key copy

        @Steps:

        1. Copy Activation key by passing name of parent

        @Assert: Activation key is sucessfully copied

        """
        parent_name = make_activation_key(
            {u'organization-id': self.org['id']},
            cached=True,
        )['name']
        result = ActivationKey.copy({
            u'name': parent_name,
            u'new-name': gen_string('alpha'),
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result[0], u'Activation key copied')

    @tier1
    def test_negative_copy_with_same_name(self):
        """@Test: Copy activation key with duplicate name

        @Feature: Activation key copy

        @Steps:

        1. Attempt to copy an activation key with a duplicate name

        @Assert: Activation key not successfully copied

        """
        parent_name = make_activation_key(
            {u'organization-id': self.org['id']},
            cached=True,
        )['name']
        with self.assertRaises(CLIReturnCodeError) as exe:
            ActivationKey.copy({
                u'name': parent_name,
                u'new-name': parent_name,
                u'organization-id': self.org['id'],
            })
        self.assertEqual(exe.exception.return_code, 65)
        self.assertIn(u'Name has already been taken', exe.exception.stderr)

    @tier2
    def test_positive_copy_subscription(self):
        """@Test: Copy Activation key and verify contents

        @Feature: Activation key copy

        @Steps:

        1. Create parent key and add content
        2. Copy Activation key by passing id of parent
        3. Verify content was sucessfully copied

        @Assert: Activation key is sucessfully copied

        """
        # Begin test setup
        org_id = make_org()['id']
        parent_id = make_activation_key({
            u'organization-id': org_id
        })['id']
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        Subscription.upload({
            'file': manifest,
            'organization-id': org_id,
        })
        subscription_result = Subscription.list(
            {'organization-id': org_id}, per_page=False)
        ActivationKey.add_subscription({
            u'id': parent_id,
            u'subscription-id': subscription_result[0]['id'],
        })
        # End test setup
        new_name = gen_string('utf8')
        result = ActivationKey.copy({
            u'id': parent_id,
            u'new-name': new_name,
            u'organization-id': org_id,
        })
        self.assertEqual(result[0], u'Activation key copied')
        result = ActivationKey.subscriptions({
            u'name': new_name,
            u'organization-id': org_id,
        })
        # Verify that the subscription copied over
        self.assertIn(
            subscription_result[0]['name'],  # subscription name
            result[3]  # subscription list
        )

    @tier1
    def test_positive_update_autoattach_toggle(self):
        """@Test: Update Activation key with inverse auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Get the key's current auto attach value.
        2. Update the key with the value's inverse.
        3. Verify key was updated.

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        key = make_activation_key(
            {u'organization-id': org_id},
            cached=True,
        )
        attach_value = key['auto-attach']
        # invert value
        new_value = u'false' if attach_value == u'true' else u'true'
        ActivationKey.update({
            u'auto-attach': new_value,
            u'id': key['id'],
            u'organization-id': org_id,
        })
        attach_value = ActivationKey.info({
            u'id': key['id'],
            u'organization-id': org_id,
        })['auto-attach']
        self.assertEqual(attach_value, new_value)

    @tier1
    def test_positive_update_autoattach(self):
        """@Test: Update Activation key with valid auto-attach values

        @Feature: Activation key update / info

        @Steps:

        1. Update the key with a valid value
        2. Verify key was updated.

        @Assert: Activation key is successfully copied

        """
        org_id = make_org(cached=True)['id']
        key_id = make_activation_key(
            {u'organization-id': org_id},
            cached=True,
        )['id']
        for new_value in (u'1', u'0', u'true', u'false', u'yes', u'no'):
            with self.subTest(new_value):
                result = ActivationKey.update({
                    u'auto-attach': new_value,
                    u'id': key_id,
                    u'organization-id': org_id,
                })
                self.assertEqual(
                    u'Activation key updated', result[0]['message'])

    @tier1
    def test_negative_update_autoattach(self):
        """@Test: Attempt to update Activation key with bad auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Attempt to update a key with incorrect auto-attach value
        2. Verify that an appropriate error message was returned

        @Assert: Activation key is successfully copied

        """
        org_id = make_org(cached=True)['id']
        key_id = make_activation_key(
            {u'organization-id': org_id},
            cached=True,
        )['id']
        with self.assertRaises(CLIReturnCodeError) as exe:
            ActivationKey.update({
                u'auto-attach': gen_string('utf8'),
                u'id': key_id,
                u'organization-id': org_id,
            })
        self.assertIn(
            u"'--auto-attach': value must be one of", exe.exception.stderr)

    @tier1
    @skip_if_bug_open('bugzilla', 1180282)
    def test_positive_content_override(self):
        """@Test: Positive content override

        @Feature: Activation key copy

        @Steps:

        1. Create activation key and add content
        2. Get the first product's label
        3. Override the product's content enablement
        4. Verify that the command succeeded

        @BZ: 1180282

        @Assert: Activation key content override was successful

        """
        if self.pub_key is None:
            self._make_public_key()
        result = ActivationKey.product_content({
            u'id': self.pub_key['key_id'],
            u'organization-id': self.pub_key['org_id'],
        })
        for override_value in (u'1', u'0'):
            with self.subTest(override_value):
                result = ActivationKey.content_override({
                    u'content-label': result[0]['label'],
                    u'id': self.pub_key['key_id'],
                    u'organization-id': self.pub_key['org_id'],
                    u'value': override_value,
                })
                # Retrieve the product content enabled flag
                result = ActivationKey.product_content({
                    u'id': self.pub_key['key_id'],
                    u'organization-id': self.pub_key['org_id'],
                })
                self.assertEqual(result[0]['enabled?'], override_value)
