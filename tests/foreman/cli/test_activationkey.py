# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Activation key CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_view,
    make_lifecycle_environment,
    make_org, make_product,
    make_host_collection
)
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.test import CLITestCase
from robottelo.cli.subscription import Subscription
from robottelo.common import manifests
from robottelo.common.ssh import upload_file


@ddt
class TestActivationKey(CLITestCase):
    """Activation Key CLI tests"""

    org = None
    library = None
    product = None
    env1 = None
    env2 = None

    def setUp(self):
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
        if (
                not options.get('organization', None)
                and not options.get('organization-label', None)
                and not options.get('organization-id', None)):
            options['organization-id'] = self.org['id']

        # Create activation key
        ackey = make_activation_key(options)

        # Fetch it
        result = ActivationKey.info(
            {
                'id': ackey['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Activation key was not found: %s" % str(result.stderr))
        self.assertEqual(
            len(result.stderr),
            0,
            "No error was expected %s" % str(result.stderr))

        # Return the activation key dictionary
        return ackey

    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_create_activation_key_1(self, test_data):
        """@Test: Create Activation key for all variations of
            Activation key name

        @Feature: Activation key

        @Steps:
        1. Create Activation key for all valid Activation Key name variation

        @Assert: Activation key is created with chosen name

        """

        new_ackey = self._make_activation_key({u'name': test_data['name']})
        # Name should match passed data
        self.assertEqual(
            new_ackey['name'],
            test_data['name'],
            ("Names don't match: '%s' != '%s'" %
             (new_ackey['name'], test_data['name']))
        )

    @data(
        {'description': gen_string('alpha', 15)},
        {'description': gen_string('alphanumeric', 15)},
        {'description': gen_string('numeric', 15)},
        {'description': gen_string('latin1', 15)},
        {'description': gen_string('utf8', 15)},
        {'description': gen_string('html', 15)},
    )
    def test_positive_create_activation_key_2(self, test_data):
        """@Test: Create Activation key for all variations of Description

        @Feature: Activation key

        @Steps:
        1. Create Activation key for all valid Description variation

        @Assert: Activation key is created with chosen description

        """

        new_ackey = self._make_activation_key(
            {u'description': test_data['description']})
        # Description should match passed data
        self.assertEqual(
            new_ackey['description'],
            test_data['description'],
            ("Descriptions don't match: '%s' != '%s'" %
             (new_ackey['description'], test_data['description']))
        )

    @run_only_on('sat')
    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_create_associate_environ_1(self, test_data):
        """@Test: Create Activation key and associate with Library environment

        @Feature: Activation key

        @Steps:
        1. Create Activation key for variations of Name / associated to Library

        @Assert: Activation key is created and associated to Library

        """

        new_ackey = self._make_activation_key(
            {u'name': test_data['name'],
             u'lifecycle-environment-id': self.library['id']})
        # Description should match passed data
        self.assertEqual(
            new_ackey['lifecycle-environment'],
            self.library['name'],
            ("Environments don't match: '%s' != '%s'" %
             (new_ackey['lifecycle-environment'], self.library['name']))
        )

    @run_only_on('sat')
    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_create_associate_environ_2(self, test_data):
        """@Test: Create Activation key and associate with environment

        @Feature: Activation key

        @Steps:
        1. Create Activation key for variations of Name / associated to environ

        @Assert: Activation key is created and associated to environment

        """

        new_ackey = self._make_activation_key(
            {u'name': test_data['name'],
             u'lifecycle-environment-id': self.env1['id']})
        # Description should match passed data
        self.assertEqual(
            new_ackey['lifecycle-environment'],
            self.env1['name'],
            ("Environments don't match: '%s' != '%s'" %
             (new_ackey['lifecycle-environment'], self.env1['name']))
        )

    @data(

        {'name': gen_string("alpha", 10),
         'content-view': gen_string("alpha", 10)},
        {'name': gen_string("alphanumeric", 10),
         'content-view': gen_string("alpha", 10)},
        {'name': gen_string("numeric", 10),
         'content-view': gen_string("alpha", 10)},
        {'name': gen_string("html", 10),
         'content-view': gen_string("alpha", 10)},
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
        self.assertEqual(
            new_ackey['name'],
            test_data['name'],
            ("Names don't match: '%s' != '%s'" %
             (new_ackey['name'], test_data['name']))
        )
        # ContentView should match passed data
        self.assertEqual(
            new_ackey['content-view'],
            test_data['content-view'],
            ("Content View don't match: '%s' != '%s'" %
             (new_ackey['content-view'], test_data['content-view']))
        )

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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
    @skip_if_bug_open('bugzilla', 1109648)
    def test_positive_create_9(self):
        """@test: Create Activation key with environment name

        @feature: Activation key - Positive Create

        @steps:
        1. Create Activation key by entering its name, a content view and a
        environment name.

        @assert: Activation key is created

        @bz: 1109648

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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @skip_if_bug_open('bugzilla', 1109650)
    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_delete_activation_key_1(self, test_data):
        """@Test: Create Activation key and delete it for all variations of
        Activation key name

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Activation Key names in [1]
        using valid Description, Environment, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        @bz: 1109650

        """
        try:
            activation_key = self._make_activation_key({
                u'name': test_data['name'],
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({'id': activation_key['id']})
        self.assertEqual(
            result.return_code, 0, 'Failed to delete activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        # Can we find the object?
        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(
            result.return_code, 0, 'Activation key should be deleted')
        self.assertGreater(
            len(result.stderr), 0, 'There should be an error here')
        self.assertEqual(
            len(result.stdout), 0, 'Output should be blank')

    @skip_if_bug_open('bugzilla', 1109650)
    @data(
        {'description': gen_string('alpha', 15)},
        {'description': gen_string('alphanumeric', 15)},
        {'description': gen_string('numeric', 15)},
        {'description': gen_string('latin1', 15)},
        {'description': gen_string('utf8', 15)},
        {'description': gen_string('html', 15)},
    )
    def test_positive_delete_activation_key_2(self, test_data):
        """@Test: Create Activation key and delete it for all variations of
        Description

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Description in [1]
        using valid Name, Environment, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        @bz: 1109650

        """
        try:
            activation_key = self._make_activation_key({
                u'description': test_data['description'],
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.delete({'id': activation_key['id']})
        self.assertEqual(
            result.return_code, 0, 'Failed to delete activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        # Can we find the object?
        result = ActivationKey.info({'id': activation_key['id']})
        self.assertNotEqual(
            result.return_code, 0, 'Activation key should be deleted')
        self.assertGreater(
            len(result.stderr), 0, 'There should be an error here')
        self.assertEqual(
            len(result.stdout), 0, 'Output should be blank')

    @stubbed
    def test_positive_delete_activation_key_3(self):
        """@Test: Create Activation key and delete it for all variations of
        Environment

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        @Status: Manual

        """
        pass

    @stubbed
    def test_positive_delete_activation_key_4(self):
        """@Test: Create Activation key and delete it for all variations of
        Content Views

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Content Views in [1]
        using valid Name, Description, Environment, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        @Status: Manual

        """
        pass

    @stubbed
    def test_positive_delete_activation_key_5(self):
        """@Test: Delete an Activation key which has registered systems

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key
        2. Register systems to it
        3. Delete the Activation key

        @Assert: Activation key is deleted

        @Status: Manual

        """
        pass

    @stubbed
    def test_positive_delete_activation_key_6(self):
        """@Test: Delete a Content View associated to an Activation Key deletes
        the Activation Key

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key with a Content View
        2. Delete the Content View

        @Assert: Activation key is deleted or updated accordingly

        @Status: Manual

        """
        pass

    @stubbed
    def test_negative_delete_activation_key_1(self):
        """@Test: [UI ONLY] Attempt to delete an Activation Key and cancel it

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key
        2. Attempt to remove an Activation Key
        3. Click Cancel in the confirmation dialog box

        @Assert: Activation key is not deleted

        @Status: Manual

        """
        pass  # Skip for CLI as this is UI only

    @skip_if_bug_open('bugzilla', 1114109)
    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_update_activation_key_1(self, test_data):
        """@Test: Update Activation Key Name in Activation key searching by ID

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        @bz: 1114109

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'id': activation_key['id'],
            u'new-name': test_data['name'],
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
        self.assertEqual(result.stdout['name'], test_data['name'],
                         'Activation key name was not updated')

    @skip_if_bug_open('bugzilla', 1109649)
    @data(
        {'name': gen_string('alpha', 15)},
        {'name': gen_string('alphanumeric', 15)},
        {'name': gen_string('numeric', 15)},
        {'name': gen_string('latin1', 15)},
        {'name': gen_string('utf8', 15)},
        {'name': gen_string('html', 15)},
    )
    def test_positive_update_activation_key_2(self, test_data):
        """@Test: Update Activation Key Name in an Activation key searching by
        name

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        @bz: 1109649

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'name': activation_key['name'],
            u'new-name': test_data['name'],
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
        self.assertEqual(result.stdout['name'], test_data['name'],
                         'Activation key name was not updated')

    @skip_if_bug_open('bugzilla', 1109649)
    @data(
        {'description': gen_string('alpha', 15)},
        {'description': gen_string('alphanumeric', 15)},
        {'description': gen_string('numeric', 15)},
        {'description': gen_string('latin1', 15)},
        {'description': gen_string('utf8', 15)},
        {'description': gen_string('html', 15)},
    )
    def test_positive_update_activation_key_3(self, test_data):
        """@Test: Update Description in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [1]

        @Assert: Activation key is updated

        @bz: 1109649

        """
        try:
            activation_key = self._make_activation_key({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ActivationKey.update({
            u'name': activation_key['name'],
            u'description': test_data['description'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to update activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertEqual(
            result.stdout['description'], test_data['description'],
            'Activation key description was not updated')

    @run_only_on('sat')
    @stubbed
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
        {'content-view': gen_string('alpha', 15)},
        {'content-view': gen_string('alphanumeric', 15)},
        {'content-view': gen_string('numeric', 15)},
        {'content-view': gen_string('latin1', 15)},
        {'content-view': gen_string('utf8', 15)},
        {'content-view': gen_string('html', 15)},
    )
    def test_positive_update_activation_key_5(self, test_data):
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
                u'name': test_data['content-view']
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
            len(result.stderr), 0, 'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertEqual(
            result.stdout['content-view'], test_data['content-view'],
            'Activation key content-view was not updated')

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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
        {'host-col': gen_string('alpha', 15)},
        {'host-col': gen_string('alphanumeric', 15)},
        {'host-col': gen_string('numeric', 15)},
        {'host-col': gen_string('latin1', 15)},
        {'host-col': gen_string('utf8', 15)},
        {'host-col': gen_string('html', 15)},
    )
    def test_associate_host(self, test_data):
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
            new_host_col = make_host_collection({
                'name': test_data['host-col']
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Assert that name matches data passed
            self.assertEqual(
                new_host_col['name'],
                test_data['host-col'],
                "Names don't match"
            )

        result = ActivationKey.add_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col['name'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to add host-col activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertEqual(
            result.stdout['host-collection'], test_data['host-col'],
            'Activation key host-collection added')

    @stubbed
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
    @stubbed
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
    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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
    @stubbed
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

    @skip_if_bug_open('bugzilla', 1111723)
    def test_bugzilla_1111723(self):
        """@test: Create activation key, rename it and create another with the
        initial name

        @feature: Activation key - Positive Create

        @steps:
        1. Create an activation key
        2. Rename it
        3. Create another activation key with the same name from step 1

        @assert: Activation key is created

        @bz: 1111723

        """
        name = gen_string('utf8', 15)

        try:
            activation_key = self._make_activation_key({
                u'name': name,
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        new_name = gen_string('utf8', 15)
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
                ('Failed to create an activation key with a previous name of'
                 'another activation key: {0}').format(err))

        result = ActivationKey.info({
            u'id': new_activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Failed to get info for activation key'
        )
        self.assertEqual(
            len(result.stderr), 0,
            'There should not be an error here'
        )
        self.assertEqual(
            result.stdout['name'], name,
            u"Activation key names don't not match {0} != {1}".format(
                result.stdout['name'], name
            )
        )

    @skip_if_bug_open('bugzilla', 1110467)
    @data(
        {'host-col': gen_string('alpha', 15)},
        {'host-col': gen_string('alphanumeric', 15)},
        {'host-col': gen_string('numeric', 15)},
        {'host-col': gen_string('latin1', 15)},
        {'host-col': gen_string('utf8', 15)},
        {'host-col': gen_string('html', 15)},
    )
    def test_remove_host(self, test_data):
        """@Test: Test that hosts associated to Activation Keys can be removed

        @Feature: Activation key - Host

        @Steps:
        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key
        4. Remove the hosts associated to Activation key

        @Assert: Hosts successfully removed that
        are associated to Activation key

        """
        try:
            org = make_org(cached=True)
            activation_key = self._make_activation_key({
                u'organization-id': org['id'],
            })
            new_host_col = make_host_collection({
                u'name': test_data['host-col'],
                u'organization-id': org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Assert that name matches data passed
        self.assertEqual(new_host_col['name'],
                         test_data['host-col'],
                         "Names don't match")

        result = ActivationKey.add_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col['name'],
            u'organization-id': org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to add host-col activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertEqual(
            result.stdout['host-collections'][0]['name'],
            test_data['host-col'],
            'Activation key host-collection added')

        result = ActivationKey.remove_host_collection({
            u'name': activation_key['name'],
            u'host-collection': new_host_col['name'],
            u'organization-id': org['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to remove host-col activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')

        result = ActivationKey.info({
            u'id': activation_key['id'],
        })
        self.assertEqual(
            result.return_code, 0, 'Failed to get info for activation key')
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertEqual(
            len(result.stdout['host-collections']), 0,
            'Activation key host-collection removed')

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
            org = make_org(cached=True)
            activation_key = self._make_activation_key({
                u'organization-id': org['id'],
            })
            result = Subscription.upload({
                'file': manifest,
                'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        subs_id = Subscription.list(
            {'organization-id': self.org['id']},
            per_page=False)

        result = ActivationKey.add_subscription({
            u'id': activation_key['id'],
            u'subscription-id': subs_id.stdout[0]['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "return code must be 0, instead got {0}"
                         ''.format(result.return_code))
        self.assertEqual(
            len(result.stderr), 0, 'There should not be an error here')
        self.assertIn("Subscription added to activation key",
                      result.stdout)

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
        org_id = make_org(cached=True)['id']
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
        self.assertEqual(result.return_code, 0,
                         'Test failed during setup. Return code: {0}'
                         ', expected 0'.format(result.return_code))
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
        key_id = make_activation_key(
            {u'organization-id': org_id}, cached=True)['id']
        try:
            attach_value = ActivationKey.info({
                u'id': key_id,
                u'organization-id': org_id,
            }).stdout['auto-attach']
        except CLIFactoryError as err:
            self.fail(err)
        # invert value
        new_value = u'false' if attach_value == u'true' else u'true'
        try:
            result = ActivationKey.update({
                u'auto-attach': new_value,
                u'id': key_id,
                u'organization-id': org_id,
            })
            self.assertEqual(result.return_code, 0)
            attach_value = ActivationKey.info({
                u'id': key_id,
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

        self.assertIn("'--auto-attach': value must be one of", result.stderr)
