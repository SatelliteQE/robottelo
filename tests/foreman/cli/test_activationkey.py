# -*- encoding: utf-8 -*-
"""Test class for Activation key CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo import manifests
from robottelo.cli.activationkey import ActivationKey
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
from robottelo.decorators import (
    bz_bug_is_open, data, run_only_on,
    skip_if_bug_open, stubbed
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


@ddt
class TestActivationKey(CLITestCase):
    """Activation Key CLI tests"""
    org = None
    library = None
    product = None
    env1 = None
    env2 = None
    pub_key = None

    def setUp(self):  # noqa
        """Tests for activation keys via Hammer CLI"""
        super(TestActivationKey, self).setUp()

        if TestActivationKey.org is None:
            TestActivationKey.org = make_org(cached=True)
        if TestActivationKey.env1 is None:
            TestActivationKey.env1 = make_lifecycle_environment(
                {u'organization-id': TestActivationKey.org['id']},
                cached=True)
        if TestActivationKey.env2 is None:
            TestActivationKey.env2 = make_lifecycle_environment(
                {u'organization-id': TestActivationKey.org['id'],
                 u'prior': TestActivationKey.env1['label']})
        if TestActivationKey.product is None:
            TestActivationKey.product = make_product(
                {u'organization-id': TestActivationKey.org['id']},
                cached=True)
        if TestActivationKey.library is None:
            TestActivationKey.library = LifecycleEnvironment.info(
                {'organization-id': TestActivationKey.org['id'],
                 'name': 'Library'}).stdout

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
        if TestActivationKey.pub_key is None:
            TestActivationKey.pub_key = {}
            try:
                organization_id = make_org()['id']
                TestActivationKey.pub_key['org_id'] = organization_id
                TestActivationKey.pub_key['prod_id'] = make_product({
                    'organization-id': organization_id,
                })['id']
                TestActivationKey.pub_key['manifest'] = manifests.clone()

                upload_file(TestActivationKey.pub_key['manifest'])
                Subscription.upload({
                    'file': TestActivationKey.pub_key['manifest'],
                    'organization-id': TestActivationKey.pub_key['org_id'],
                })

                # create content view
                TestActivationKey.pub_key['content_view_id'] = (
                    make_content_view({
                        u'organization-id': (
                            TestActivationKey.pub_key['org_id']),
                        u'name': gen_string('alpha'),
                    })['id']
                )

                TestActivationKey.pub_key['repo_id'] = make_repository({
                    u'product-id': TestActivationKey.pub_key['prod_id'],
                })['id']

                Repository.synchronize({
                    'id': TestActivationKey.pub_key['repo_id'],
                    'organization-id': TestActivationKey.pub_key['org_id'],
                })

                ContentView.add_repository({
                    u'id': TestActivationKey.pub_key['content_view_id'],
                    u'repository-id': TestActivationKey.pub_key['repo_id'],
                })

                ContentView.publish({
                    u'id': TestActivationKey.pub_key['content_view_id'],
                })

                TestActivationKey.pub_key['key_id'] = make_activation_key({
                    u'organization-id': TestActivationKey.pub_key['org_id']
                })['id']

                subscription_result = Subscription.list({
                    'organization-id': TestActivationKey.pub_key['org_id'],
                    'order': 'id desc'},
                    per_page=False
                )

                ActivationKey.add_subscription({
                    u'id': TestActivationKey.pub_key['key_id'],
                    u'subscription-id': subscription_result.stdout[-1]['id'],
                })
            except CLIFactoryError as err:
                TestActivationKey.pub_key = None
                self.fail(err)

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_create_activation_key_1(self, name):
        """@Test: Create Activation key for all variations of
            Activation key name

        @Feature: Activation key

        @Steps:

        1. Create Activation key for all valid Activation Key name variation

        @Assert: Activation key is created with chosen name

        """
        new_ackey_name = self._make_activation_key({u'name': name})['name']
        # Name should match passed data
        self.assertEqual(new_ackey_name, name)

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_create_activation_key_2(self, description):
        """@Test: Create Activation key for all variations of Description

        @Feature: Activation key

        @Steps:

        1. Create Activation key for all valid Description variation

        @Assert: Activation key is created with chosen description

        """
        new_ackey_description = self._make_activation_key(
            {u'description': description})['description']
        # Description should match passed data
        self.assertEqual(new_ackey_description, description)

    @run_only_on('sat')
    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_create_associate_environ_1(self, name):
        """@Test: Create Activation key and associate with Library environment

        @Feature: Activation key

        @Steps:

        1. Create Activation key for variations of Name / associated to Library

        @Assert: Activation key is created and associated to Library

        """
        new_ackey_env = self._make_activation_key(
            {u'name': name,
             u'lifecycle-environment-id': self.library['id']}
        )['lifecycle-environment']
        # Description should match passed data
        self.assertEqual(new_ackey_env, self.library['name'])

    @run_only_on('sat')
    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_create_associate_environ_2(self, name):
        """@Test: Create Activation key and associate with environment

        @Feature: Activation key

        @Steps:

        1. Create Activation key for variations of Name / associated to environ

        @Assert: Activation key is created and associated to environment

        """
        new_ackey_env = self._make_activation_key({
            u'name': name,
            u'lifecycle-environment-id': self.env1['id']
        })['lifecycle-environment']
        # Description should match passed data
        self.assertEqual(new_ackey_env, self.env1['name'])

    @data(
        {'name': gen_string('alpha'),
         'content-view': gen_string('alpha')},
        {'name': gen_string('alphanumeric'),
         'content-view': gen_string('alpha')},
        {'name': gen_string('numeric'),
         'content-view': gen_string('alpha')},
        {'name': gen_string('html'),
         'content-view': gen_string('alpha')},
    )
    def test_positive_create_activation_key_4(self, test_data):
        """@Test: Create Activation key for all variations of Content Views

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit

        @Assert: Activation key is created

        """
        try:
            org_obj = make_org(cached=True)
            con_view = make_content_view({
                u'organization-id': org_obj['id'],
                u'name': test_data['content-view']
            })
            new_ackey = self._make_activation_key({
                u'name': test_data['name'],
                u'content-view': con_view['name'],
                u'environment': self.library['name'],
                u'organization-id': org_obj['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Name should match passed data
        self.assertEqual(new_ackey['name'], test_data['name'])
        # ContentView should match passed data
        self.assertEqual(new_ackey['content-view'], test_data['content-view'])

    @stubbed()
    def test_positive_create_activation_key_5(self):
        """@Test: Create Activation key for all variations of System Groups

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key for all valid System Groups in [1]
        using valid Name, Description, Environment, Content View, Usage limit

        @Assert: Activation key is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_activation_key_6(self):
        """@Test: Create Activation key with default Usage limit (Unlimited)

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_activation_key_7(self):
        """@Test: Create Activation key with finite Usage limit

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_create_activation_key_8(self):
        """@Test: Create Activation key with minimal input parameters

        @Feature: Activation key - Positive Create

        @Steps:

        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values

        @Assert: Activation key is created

        @Status: Manual

        """
        pass

    @run_only_on('sat')
    def test_positive_create_9(self):
        """@test: Create Activation key with environment name

        @feature: Activation key - Positive Create

        @steps:

        1. Create Activation key by entering its name, a content view and a
        environment name.

        @assert: Activation key is created

        """
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })

        try:
            self._make_activation_key({
                u'content-view': content_view['name'],
                u'environment': self.library['name'],
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

    @stubbed()
    def test_negative_create_activation_key_1(self):
        """@Test: Create Activation key with invalid Name

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Activation Key Names in [2]
        using valid Description, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_create_activation_key_2(self):
        """@Test: Create Activation key with invalid Description

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Description in [2]
        using valid Name, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_create_activation_key_3(self):
        """@Test: Create Activation key with invalid Usage Limit

        @Feature: Activation key - Negative Create

        @Steps:

        1. Create Activation key for all invalid Usage Limit in [2]
        using valid Name, Description, Environment, Content View

        @Assert: Activation key is not created. Appropriate error shown.

        @Status: Manual

        """
        pass

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_delete_activation_key_by_name(self, name):
        """@Test: Create Activation key and delete it for all variations of
        Activation key name

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key for all valid Activation Key names
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        try:
            activation_key = self._make_activation_key({
                u'name': name,
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({
            'name': activation_key['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(result.return_code, 0)

    def test_delete_activation_key_by_org_name(self):
        """@Test: Create Activation key and delete it using organization name
        for which that key was created

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key
        2. Delete Activation key using organization name

        @Assert: Activation key is deleted

        """
        try:
            activation_key = self._make_activation_key({
                u'name': gen_string('alpha'),
                u'description': gen_string('alpha'),
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({
            'name': activation_key['name'],
            'organization': self.org['name'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(result.return_code, 0)

    def test_delete_activation_key_by_org_label(self):
        """@Test: Create Activation key and delete it using organization
        label for which that key was created

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key
        2. Delete Activation key using organization label

        @Assert: Activation key is deleted

        """
        try:
            activation_key = self._make_activation_key({
                u'name': gen_string('alpha'),
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({
            'name': activation_key['name'],
            'organization-label': self.org['label'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(result.return_code, 0)

    def test_delete_activation_key_with_content_view(self):
        """@Test: Create activation key with content view assigned to it and delete
        it using activation key id

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key with content view assigned to it
        2. Delete Activation key using activation key id

        @Assert: Activation key is deleted

        """
        try:
            cv = make_content_view({u'organization-id': self.org['id']})
            activation_key = self._make_activation_key({
                u'name': gen_string('alpha'),
                u'content-view': cv['name'],
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(result.return_code, 0)

    def test_delete_activation_key_with_lifecycle_environment(self):
        """@Test: Create activation key with lifecycle environment assigned to
        it and delete it using activation key id

        @Feature: Activation key - Positive Delete

        @Steps:

        1. Create Activation key with lifecycle environment assigned to it
        2. Delete Activation key using activation key id

        @Assert: Activation key is deleted

        """
        try:
            env = make_lifecycle_environment({
                u'organization-id': self.org['id'],
            })
            activation_key = self._make_activation_key({
                u'name': gen_string('alpha'),
                u'lifecycle-environment': env['name'],
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(result.return_code, 0)

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_update_activation_key_1(self, name):
        """@Test: Update Activation Key Name in Activation key searching by ID

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'id': activation_key['id'],
            u'new-name': name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to update activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to get info for activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')
        self.assertEqual(result.stdout['name'], name,
                         'Activation key name was not updated')

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_update_activation_key_2(self, name):
        """@Test: Update Activation Key Name in an Activation key searching by
        name

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'name': activation_key['name'],
            u'new-name': name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to update activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to get info for activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')
        self.assertEqual(result.stdout['name'], name,
                         'Activation key name was not updated')

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_update_activation_key_3(self, description):
        """@Test: Update Description in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Description for all variations in [1]

        @Assert: Activation key is updated

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'name': activation_key['name'],
            u'description': description,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to update activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)
        self.assertEqual(
            result.stdout['description'], description,
            'Activation key description was not updated')

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_activation_key_4(self):
        """@Test: Update Environment in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Environment for all variations in [1]

        @Assert: Activation key is updated

        @Status: Manual

        """
        pass

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1109649)
    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_update_activation_key_5(self, content_view):
        """@Test: Update Content View in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Content View for all variations in [1] and include both
           RH and custom products

        @Assert: Activation key is updated

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
            con_view = make_content_view({
                u'organization-id': self.org['id'],
                u'name': content_view
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'name': activation_key['name'],
            u'content-view': con_view['name'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to update activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)
        self.assertEqual(
            result.stdout['content-view'], content_view,
            'Activation key content-view was not updated')

    @stubbed()
    def test_positive_update_activation_key_6(self):
        """@Test: Update Usage limit from Unlimited to a finite number

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Usage limit from Unlimited to a definite number

        @Assert: Activation key is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_positive_update_activation_key_7(self):
        """@Test: Update Usage limit from definite number to Unlimited

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create Activation key
        2. Update Usage limit from definite number to Unlimited

        @Assert: Activation key is updated

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_update_activation_key_1(self):
        """@Test: Update invalid name in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Activation key name for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_update_activation_key_2(self):
        """@Test: Update invalid Description in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Description for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """
        pass

    @stubbed()
    def test_negative_update_activation_key_3(self):
        """@Test: Update invalid Usage Limit in an activation key

        @Feature: Activation key - Negative Update

        @Steps:

        1. Create Activation key
        2. Update Usage Limit for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @Status: Manual

        """
        pass

    @stubbed()
    def test_usage_limit(self):
        """@Test: Test that Usage limit actually limits usage

        @Feature: Activation key - Usage limit

        @Steps:

        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Systems to match the Usage Limit
        4. Attempt to register an other system after reaching the Usage Limit

        @Assert: System Registration fails. Appropriate error shown

        @Status: Manual

        """
        pass

    @skip_if_bug_open('bugzilla', 1110476)
    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_associate_host(self, host_col):
        """@Test: Test that hosts can be associated to Activation Keys

        @Feature: Activation key - Host

        @Steps:

        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key

        @Assert: Hosts are successfully associated to Activation key

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
            new_host_col_name = make_host_collection({
                'name': host_col
            })['name']
        except CLIFactoryError as err:
            self.fail(err)

        # Assert that name matches data passed
            self.assertEqual(
                new_host_col_name,
                host_col,
                'Names don\'t match'
            )

        result = ActivationKey.add_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col_name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to add host-col activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, result.stderr)
        self.assertEqual(
            result.stdout['host-collection'], host_col,
            'Activation key host-collection added')

    @stubbed()
    def test_associate_product_1(self):
        """@Test: Test that RH product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key

        @Assert: RH products are successfully associated to Activation key

        @Status: Manual

        """
        pass

    @run_only_on('sat')
    @stubbed()
    def test_associate_product_2(self):
        """@Test: Test that custom product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate custom product(s) to Activation Key

        @Assert: Custom products are successfully associated to Activation key

        @Status: Manual

        """
        pass

    @run_only_on('sat')
    @stubbed()
    def test_associate_product_3(self):
        """@Test: Test if RH/Custom product can be associated to Activation key

        @Feature: Activation key - Product

        @Steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @Assert: RH/Custom product is successfully associated to Activation key

        @Status: Manual

        """
        pass

    @stubbed()
    def test_delete_manifest(self):
        """@Test: Check if deleting a manifest removes it from Activation key

        @Feature: Activation key - Manifest

        @Steps:

        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest

        @Assert: Deleting a manifest removes it from the Activation key

        @Status: Manual

        """
        pass

    @stubbed()
    def test_multiple_activation_keys_to_system(self):
        """@Test: Check if multiple Activation keys can be attached to a system

        @Feature: Activation key - System

        @Steps:

        1. Create multiple Activation keys
        2. Attach all the created Activation keys to a System

        @Assert: Multiple Activation keys are attached to a system

        @Status: Manual

        """
        pass

    @stubbed()
    def test_list_activation_keys_1(self):
        """@Test: List Activation key for all variations of Activation key name

        @Feature: Activation key - list

        @Steps:

        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. List Activation key

        @Assert: Activation key is listed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_list_activation_keys_2(self):
        """@Test: List Activation key for all variations of Description

        @Feature: Activation key - list

        @Steps:

        1. Create Activation key for all valid Description variation in [1]
        2. List Activation key

        @Assert: Activation key is listed

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_activation_keys_1(self):
        """@Test: Search Activation key for all variations of
            Activation key name

        @Feature: Activation key - search

        @Steps:

        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. Search/find Activation key

        @Assert: Activation key is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_search_activation_keys_2(self):
        """@Test: Search Activation key for all variations of Description

        @Feature: Activation key - search

        @Steps:

        1. Create Activation key for all valid Description variation in [1]
        2. Search/find Activation key

        @Assert: Activation key is found

        @Status: Manual

        """
        pass

    @stubbed()
    def test_info_activation_keys_1(self):
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
        pass

    @stubbed()
    def test_info_activation_keys_2(self):
        """@Test: Get Activation key info for all variations of Description

        @Feature: Activation key - info

        @Steps:

        1. Create Activation key for all valid Description variation in [1]
        2. Get info of the Activation key

        @Assert: Activation key info is displayed

        @Status: Manual

        """
        pass

    @run_only_on('sat')
    @stubbed()
    def test_end_to_end(self):
        """@Test: Create Activation key and provision systems with it

        @Feature: Activation key - End to End

        @Steps:

        1. Create Activation key
        2. Provision systems with Activation key

        @Assert: Systems are successfully provisioned with Activation key

        @Status: Manual

        """
        pass

    def test_bugzilla_1111723(self):
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

        try:
            activation_key = self._make_activation_key({
                u'name': name,
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        new_name = gen_string('utf8')
        result = ActivationKey.update({
            u'id': activation_key['id'],
            u'new-name': new_name,
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to update activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(result.return_code, 0,
                         'Failed to get info for activation key')
        self.assertEqual(len(result.stderr), 0,
                         'There should not be an error here')
        self.assertEqual(result.stdout['name'], new_name,
                         'Activation key name was not updated')

        try:
            new_activation_key = self._make_activation_key({
                u'name': name,
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(
                u'Failed to create an activation key with a previous name of'
                'another activation key: {0}'.format(err)
            )

        self.assertEqual(new_activation_key['name'], name)

    def test_remove_host_collection_by_id(self):
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
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
            new_host_col = make_host_collection({
                u'name': gen_string('alpha'),
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.add_host_collection({
            u'name': activation_key['name'],
            u'host-collection-id': new_host_col['id'],
            u'organization': self.org['name'],
        })
        self.assertEqual(result.return_code, 0)

        result = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['host-collections']), 1)

        result = ActivationKey.remove_host_collection({
            u'name': activation_key['name'],
            u'host-collection-id': new_host_col['id'],
            u'organization': self.org['name'],
        })
        self.assertEqual(result.return_code, 0)

        result = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['host-collections']), 0)

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_remove_host_collection_by_name(self, host_col):
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
        try:
            org_id = make_org(cached=True)['id']
            activation_key = self._make_activation_key({
                u'organization-id': org_id,
            })
            new_host_col = make_host_collection({
                u'name': host_col,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Assert that name matches data passed
        self.assertEqual(new_host_col['name'], host_col)

        result = ActivationKey.add_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col['name'],
            u'organization-id': org_id,
        })
        self.assertEqual(result.return_code, 0)

        result = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['host-collections']), 1)
        self.assertEqual(
            result.stdout['host-collections'][0]['name'],
            host_col,
        )

        result = ActivationKey.remove_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col['name'],
            u'organization-id': org_id,
        })
        self.assertEqual(result.return_code, 0)

        result = ActivationKey.info({u'id': activation_key['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['host-collections']), 0)

    def test_add_subscription(self):
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
        try:
            org_id = make_org()['id']
            activation_key_id = self._make_activation_key({
                u'organization-id': org_id,
            })['id']
            result = Subscription.upload({
                'file': manifest,
                'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        subs_id = Subscription.list(
            {'organization-id': org_id},
            per_page=False)

        result = ActivationKey.add_subscription({
            u'id': activation_key_id,
            u'subscription-id': subs_id.stdout[0]['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0, result.stderr)
        self.assertIn('Subscription added to activation key', result.stdout)

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_positive_copy_activation_key_1(self, new_name):
        """@Test: Copy Activation key for all valid Activation Key name
           variations

        @Feature: Activation key copy

        @Steps:

        1. Copy Activation key for all valid Activation Key name variations

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        parent_id = make_activation_key(
            {u'organization-id': org_id}, cached=True)['id']

        try:
            result = ActivationKey.copy({
                u'id': parent_id,
                u'new-name': new_name,
                u'organization-id': org_id
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout[0], u'Activation key copied')

    def test_positive_copy_activation_key_2(self):
        """@Test: Copy Activation key by passing name of parent

        @Feature: Activation key copy

        @Steps:

        1. Copy Activation key by passing name of parent

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        parent_name = make_activation_key(
            {u'organization-id': org_id}, cached=True)['name']

        try:
            result = ActivationKey.copy({
                u'name': parent_name,
                u'new-name': gen_string('alpha'),
                u'organization-id': org_id
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout[0], u'Activation key copied')

    def test_negative_copy_activation_key(self):
        """@Test: Copy activation key with duplicate name

        @Feature: Activation key copy

        @Steps:

        1. Attempt to copy an activation key with a duplicate name

        @Assert: Activation key not sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        parent_name = make_activation_key(
            {u'organization-id': org_id}, cached=True)['name']

        try:
            result = ActivationKey.copy({
                u'name': parent_name,
                u'new-name': parent_name,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 65)
        self.assertIn(u'Name has already been taken', result.stderr)

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
        parent_id = make_activation_key(
            {u'organization-id': org_id})['id']

        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        try:
            result = Subscription.upload({
                'file': manifest,
                'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        subscription_result = Subscription.list(
            {'organization-id': org_id}, per_page=False)

        result = ActivationKey.add_subscription({
            u'id': parent_id,
            u'subscription-id': subscription_result.stdout[0]['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Test failed during setup. Return code: {0}, expected 0'
            .format(result.return_code)
        )
        # End test setup

        new_name = gen_string('utf8')
        try:
            result = ActivationKey.copy({
                u'id': parent_id,
                u'new-name': new_name,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout[0], u'Activation key copied')

        try:
            result = ActivationKey.subscriptions({
                u'name': new_name,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 0)
        # Verify that the subscription copied over
        self.assertIn(
            subscription_result.stdout[0]['name'],  # subscription name
            result.stdout[3]  # subscription list
        )

    def test_positive_update_auto_attach(self):
        """@Test: Update Activation key with inverse auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Get the key's current auto attach value.
        2. Update the key with the value's inverse.
        3. Verify key was updated.

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        key = make_activation_key({u'organization-id': org_id}, cached=True)
        attach_value = key['auto-attach']

        # invert value
        new_value = u'false' if attach_value == u'true' else u'true'
        try:
            result = ActivationKey.update({
                u'auto-attach': new_value,
                u'id': key['id'],
                u'organization-id': org_id,
            })
            self.assertEqual(result.return_code, 0)
            attach_value = ActivationKey.info({
                u'id': key['id'],
                u'organization-id': org_id,
            }).stdout['auto-attach']
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(attach_value, new_value)

    @data(
        u'1',
        u'0',
        u'true',
        u'false',
        u'yes',
        u'no',
    )
    def test_positive_update_auto_attach_2(self, new_value):
        """@Test: Update Activation key with valid auto-attach values

        @Feature: Activation key update / info

        @Steps:

        1. Update the key with a valid value
        2. Verify key was updated.

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        key_id = make_activation_key(
            {u'organization-id': org_id}, cached=True)['id']
        try:
            result = ActivationKey.update({
                u'auto-attach': new_value,
                u'id': key_id,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            u'Activation key updated', result.stdout[0]['message'])

    def test_negative_update_auto_attach(self):
        """@Test: Attempt to update Activation key with bad auto-attach value

        @Feature: Activation key update / info

        @Steps:

        1. Attempt to update a key with incorrect auto-attach value
        2. Verify that an appropriate error message was returned

        @Assert: Activation key is sucessfully copied

        """
        org_id = make_org(cached=True)['id']
        key_id = make_activation_key(
            {u'organization-id': org_id}, cached=True)['id']
        try:
            result = ActivationKey.update({
                u'auto-attach': gen_string('utf8'),
                u'id': key_id,
                u'organization-id': org_id,
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(u"'--auto-attach': value must be one of", result.stderr)

    @skip_if_bug_open('bugzilla', 1221778)
    @data(
        u'1',
        u'0',
    )
    def test_positive_content_override(self, override_value):
        """@Test: Positive content override

        @Feature: Activation key copy

        @Steps:

        1. Create activation key and add content
        2. Get the first product's label
        3. Override the product's content enablement
        4. Verify that the command succeeded

        @Assert: Activation key content override was successful

        @BZ: 1221778

        """
        if not bz_bug_is_open(1180282):
            self.fail('BZ 1180282 has been closed. This test should be '
                      'updated to verify value change via product-content.')

        if self.pub_key is None:
            self._make_public_key()

        result = ActivationKey.product_content({
            u'id': self.pub_key['key_id'],
            u'organization-id': self.pub_key['org_id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        product_label = result.stdout[3].split('|')[5].replace(' ', '')

        result = ActivationKey.content_override({
            u'id': self.pub_key['key_id'],
            u'organization-id': self.pub_key['org_id'],
            u'content-label': product_label,
            u'value': override_value,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertIn(result.stdout[0], 'Updated content override')
