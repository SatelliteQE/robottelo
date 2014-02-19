# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Activation key UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import NOT_IMPLEMENTED, ENVIRONMENT
from robottelo.common.decorators import bzbug
from robottelo.common.helpers import generate_name, valid_names_list
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


@ddt
class ActivationKey(BaseUI):
    """
    Implements Activation key tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_activation_key_1(self, name):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Activation key name
        @Steps:
        1. Create Activation key for all valid Activation Key name variation
        in [1] using valid Description, Environment, Content View, Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=generate_name(16))
        self.assertIsNotNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_activation_key_2(self, description):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Description
        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        using valid Name, Environment, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """

        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    def test_positive_create_activation_key_3(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Environments
        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_activation_key_4(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Content Views
        @Steps:
        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_activation_key_5(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of System Groups
        @Steps:
        1. Create Activation key for all valid System Groups in [1]
        using valid Name, Description, Environment, Content View, Usage limit
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_6(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with default Usage limit (Unlimited)
        @Steps:
        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @Status: Manual
        """
        name = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_7(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with finite Usage limit
        @Steps:
        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @Status: Manual
        """
        name = generate_name(6)
        description = generate_name(6)
        limit = "6"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, limit, description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_8(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with minimal input parameters
        @Steps:
        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values
        @Assert: Activation key is created
        @Status: Manual
        """
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))

    def test_negative_create_activation_key_1(self):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Name
        @Steps:
        1. Create Activation key for all invalid Activation Key Names in [2]
        using valid Description, Environment, Content View, Usage limit
        @Assert: Activation key is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_activation_key_2(self):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Description
        @Steps:
        1. Create Activation key for all invalid Description in [2]
        using valid Name, Environment, Content View, Usage limit
        @Assert: Activation key is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_create_activation_key_3(self):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Usage Limit
        @Steps:
        1. Create Activation key for all invalid Usage Limit in [2]
        using valid Name, Description, Environment, Content View
        @Assert: Activation key is not created. Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_1(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Activation key name
        @Steps:
        1. Create Activation key for all valid Activation Key names in [1]
        using valid Description, Environment, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_2(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Description
        @Steps:
        1. Create Activation key for all valid Description in [1]
        using valid Name, Environment, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_3(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Environment
        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_4(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Content Views
        @Steps:
        1. Create Activation key for all valid Content Views in [1]
        using valid Name, Description, Environment, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_5(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Delete an Activation key which has registered systems
        @Steps:
        1. Create an Activation key
        2. Register systems to it
        3. Delete the Activation key
        @Assert: Activation key is deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_positive_delete_activation_key_6(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Delete a Content View associated to an Activation Key deletes
        the Activation Key
        @Steps:
        1. Create an Activation key with a Content View
        2. Delete the Content View
        @Assert: Activation key is deleted or updated accordingly
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @bzbug('1063273')
    def test_negative_delete_activation_key_1(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: [UI ONLY] Attempt to delete an Activation Key and cancel it
        @Steps:
        1. Create an Activation key
        2. Attempt to remove an Activation Key
        3. Click Cancel in the confirmation dialog box
        @Assert: Activation key is not deleted
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_update_activation_key_1(self, new_name):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Activation Key Name in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [1]
        @Assert: Activation key is updated
        @Status: Manual
        """

        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, new_name)
        self.assertIsNotNone(self.activationkey.search_key(new_name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_update_activation_key_2(self, new_description):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Description in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [1]
        @Assert: Activation key is updated
        @Status: Manual
        """

        name = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, description=new_description)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    def test_positive_update_activation_key_3(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Environment in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Environment for all variations in [1]
        @Assert: Activation key is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_update_activation_key_4(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Content View in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Content View for all variations in [1] and include both
        RH and custom products
        @Assert: Activation key is updated
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    @attr('ui', 'ak', 'implemented')
    def test_positive_update_activation_key_5(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Usage limit from Unlimited to a finite number
        @Steps:
        1. Create Activation key
        2. Update Usage limit from Unlimited to a definite number
        @Assert: Activation key is updated
        @Status: Manual
        """

        name = generate_name(6)
        limit = "8"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, limit=limit)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'ak', 'implemented')
    def test_positive_update_activation_key_6(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Usage limit from definite number to Unlimited
        @Steps:
        1. Create Activation key
        2. Update Usage limit from definite number to Unlimited
        @Assert: Activation key is updated
        @Status: Manual
        """

        name = generate_name(6)
        limit = "6"
        new_limit = "Unlimited"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, limit=limit)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, limit=new_limit)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    def test_negative_update_activation_key_1(self):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid name in an activation key
        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_activation_key_2(self):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid Description in an activation key
        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_negative_update_activation_key_3(self):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid Usage Limit in an activation key
        @Steps:
        1. Create Activation key
        2. Update Usage Limit for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_usage_limit(self):
        """
        @Feature: Activation key - Usage limit
        @Test: Test that Usage limit actually limits usage
        @Steps:
        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Systems to match the Usage Limit
        4. Attempt to register an other system after reaching the Usage Limit
        @Assert: System Registration fails. Appropriate error shown
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_associate_host(self):
        """
        @Feature: Activation key - Host
        @Test: Test that hosts can be associated to Activation Keys
        @Steps:
        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key
        @Assert: Hosts are successfully associated to Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_associate_product_1(self):
        """
        @Feature: Activation key - Product
        @Test: Test that RH product can be associated to Activation Keys
        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        @Assert: RH products are successfully associated to Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_associate_product_2(self):
        """
        @Feature: Activation key - Product
        @Test: Test that custom product can be associated to Activation Keys
        @Steps:
        1. Create Activation key
        2. Associate custom product(s) to Activation Key
        @Assert: Custom products are successfully associated to Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_associate_product_3(self):
        """
        @Feature: Activation key - Product
        @Test: Test that RH/Custom product can be associated to Activation keys
        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key
        @Assert: RH/Custom product is successfully associated to Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_delete_manifest(self):
        """
        @Feature: Activation key - Manifest
        @Test: Check if deleting a manifest removes it from Activation key
        @Steps:
        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest
        @Assert: Deleting a manifest removes it from the Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_multiple_activation_keys_to_system(self):
        """
        @Feature: Activation key - System
        @Test: Check if multiple Activation keys can be attached to a system
        @Steps:
        1. Create multiple Activation keys
        2. Attach all the created Activation keys to a System
        @Assert: Multiple Activation keys are attached to a system
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_activation_keys_1(self):
        """
        @Feature: Activation key - list
        @Test: List Activation key for all variations of Activation key name
        @Steps:
        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. List Activation key
        @Assert: Activation key is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_list_activation_keys_2(self):
        """
        @Feature: Activation key - list
        @Test: List Activation key for all variations of Description
        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        2. List Activation key
        @Assert: Activation key is listed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_activation_keys_1(self):
        """
        @Feature: Activation key - search
        @Test: Search Activation key for all variations of Activation key name
        @Steps:
        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. Search/find Activation key
        @Assert: Activation key is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_search_activation_keys_2(self):
        """
        @Feature: Activation key - search
        @Test: Search Activation key for all variations of Description
        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        2. Search/find Activation key
        @Assert: Activation key is found
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_activation_keys_1(self):
        """
        @Feature: Activation key - info
        @Test: Get Activation key info for all variations of Activation key
        name
        @Steps:
        1. Create Activation key for all valid Activation Key name variation
        in [1]
        2. Get info of the Activation key
        @Assert: Activation key info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_info_activation_keys_2(self):
        """
        @Feature: Activation key - info
        @Test: Get Activation key info for all variations of Description
        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        2. Get info of the Activation key
        @Assert: Activation key info is displayed
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_end_to_end_activation_key(self):
        """
        @Feature: Activation key - End to End
        @Test: Create Activation key and provision systems with it
        @Steps:
        1. Create Activation key
        2. Provision systems with Activation key
        @Assert: Systems are successfully provisioned with Activation key
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)
