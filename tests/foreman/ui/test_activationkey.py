# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Activation key UI
"""
import sys

if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import ENVIRONMENT, NOT_IMPLEMENTED
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import (generate_string, invalid_names_list,
                                      valid_names_list)
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.test import UITestCase


@ddt
class ActivationKey(UITestCase):
    """
    Implements Activation key tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name, leading and trailing
    spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    org_name = None

    def setUp(self):
        super(ActivationKey, self).setUp()
        # Make sure to use the Class' org_name instance
        if ActivationKey.org_name is None:
            ActivationKey.org_name = generate_string("alpha", 10)
            with Session(self.browser) as session:
                make_org(session, org_name=ActivationKey.org_name)

    def create_cv(self, name, env_name):
        """
        Create product/repo and sync it and promote to given env
        """

        repo_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        publish_version = "Version 1"
        publish_comment = generate_string("alpha", 8)
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)
        self.navigator.go_to_content_views()
        self.content_views.create(name)
        # Navigating to dashboard is a workaround to
        # refresh the repos under selected CV
        self.navigator.go_to_dashboard()
        self.navigator.go_to_content_views()
        self.content_views.add_remove_repos(name, [repo_name])
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.publish(name, publish_comment)
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.promote(name, publish_version, env_name)
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1078676)
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
        @BZ: 1078676
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=generate_string("alpha", 16))
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1078676)
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
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_activation_key_3(self, env):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Environments
        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View and Usage limit
        @Assert: Activation key is created
        @BZ: 1078676
        """

        name = generate_string("alpha", 8)
        cv_name = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv_name, env)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env,
                                  description=generate_string("alpha", 16),
                                  content_view=cv_name)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_create_activation_key_4(self, cv_name):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of Content Views
        @Steps:
        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit
        @Assert: Activation key is created
        @BZ: 1078676
        """

        name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv_name, env_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env_name,
                                  description=generate_string("alpha", 16),
                                  content_view=cv_name)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_positive_create_activation_key_5(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key for all variations of System Groups
        @Steps:
        1. Create Activation key for all valid System Groups in [1]
        using valid Name, Description, Environment, Content View, Usage limit
        @Assert: Activation key is created
        @Status: Manual
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_6(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with default Usage limit (Unlimited)
        @Steps:
        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @BZ: 1078676
        """
        name = generate_string("alpha", 10)
        description = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1078676)
    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_7(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with finite Usage limit
        @Steps:
        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View
        @Assert: Activation key is created
        @BZ: 1078676
        """
        name = generate_string("alpha", 10)
        description = generate_string("alpha", 10)
        limit = "6"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, limit, description)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1078676)
    @attr('ui', 'ak', 'implemented')
    def test_positive_create_activation_key_8(self):
        """
        @Feature: Activation key - Positive Create
        @Test: Create Activation key with minimal input parameters
        @Steps:
        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values
        @Assert: Activation key is created
        @BZ: 1078676
        """
        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1083471)
    @data(*invalid_names_list())
    def test_negative_create_activation_key_1(self, name):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Name
        @Steps:
        1. Create Activation key for all invalid Activation Key Names in [2]
        using valid Description, Environment, Content View, Usage limit
        @Assert: Activation key is not created. Appropriate error shown.
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        invalid = self.products.wait_until_element(common_locators
                                                   ["common_invalid"])
        self.assertTrue(invalid)
        self.assertIsNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1083438)
    def test_negative_create_activation_key_2(self):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Description
        @Steps:
        1. Create Activation key for all invalid Description in [2]
        using valid Name, Environment, Content View, Usage limit
        @Assert: Activation key is not created. Appropriate error shown.
        """

        name = generate_string("alpha", 10)
        description = generate_string("alpha", 1001)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["common_haserror"]))
        self.assertIsNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1083027)
    @data(*invalid_names_list())
    def test_negative_create_activation_key_3(self, limit):
        """
        @Feature: Activation key - Negative Create
        @Test: Create Activation key with invalid Usage Limit
        @Steps:
        1. Create Activation key for all invalid Usage Limit in [2]
        using valid Name, Description, Environment, Content View
        @Assert: Activation key is not created. Appropriate error shown.
        """
        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, limit)
        invalid = self.activationkey.wait_until_element(locators
                                                        ["ak.invalid_limit"])
        self.assertTrue(invalid)
        self.assertIsNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_activation_key_1(self, name):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Activation key name
        @Steps:
        1. Create Activation key for all valid Activation Key names in [1]
        using valid Description, Environment, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=generate_string("alpha", 16))
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.delete(name, True)
        self.assertIsNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_activation_key_2(self, description):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Description
        @Steps:
        1. Create Activation key for all valid Description in [1]
        using valid Name, Environment, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.delete(name, True)
        self.assertIsNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_activation_key_3(self, env):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Environment
        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        """

        name = generate_string("alpha", 8)
        cv_name = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv_name, env)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env,
                                  description=generate_string("alpha", 16),
                                  content_view=cv_name)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.delete(name, True)
        self.assertIsNone(self.activationkey.search_key(name))

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_delete_activation_key_4(self, cv_name):
        """
        @Feature: Activation key - Positive Delete
        @Test: Create Activation key and delete it for all variations of
        Content Views
        @Steps:
        1. Create Activation key for all valid Content Views in [1]
        using valid Name, Description, Environment, Usage limit
        2. Delete the Activation key
        @Assert: Activation key is deleted
        """

        name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv_name, env_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env_name,
                                  description=generate_string("alpha", 16),
                                  content_view=cv_name)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.delete(name, True)
        self.assertIsNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1063273)
    @unittest.skip(NOT_IMPLEMENTED)
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
        pass

    @skip_if_bug_open('bugzilla', 1117753)
    def test_positive_delete_activation_key_6(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: Delete a Content View associated to an Activation Key
        @Steps:
        1. Create an Activation key with a Content View
        2. Delete the Content View
        @Assert: Activation key should not be deleted
        @BZ: 1117753
        """
        name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 6)
        cv_name = generate_string("alpha", 6)

        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_life_cycle_environments()
            self.contentenv.create(env_name,
                                   description=generate_string("alpha", 16))
            self.assertTrue(self.contentenv.wait_until_element
                            (common_locators["alert.success"]))
            self.create_cv(cv_name, env_name)
            session.nav.go_to_activation_keys()
            self.activationkey.create(name, env_name,
                                      description=generate_string("alpha", 16),
                                      content_view=cv_name)
            self.assertIsNotNone(self.activationkey.search_key(name))
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv_name, is_affected_comps=True)
            self.content_views.delete(name, True)
            self.assertIsNone(self.content_views.search(name))
            self.assertIsNotNone(self.activationkey.search_key(name))

    def test_negative_delete_activation_key_1(self):
        """
        @Feature: Activation key - Positive Delete
        @Test: [UI ONLY] Attempt to delete an Activation Key and cancel it
        @Steps:
        1. Create an Activation key
        2. Attempt to remove an Activation Key
        3. Click Cancel in the confirmation dialog box
        @Assert: Activation key is not deleted
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=generate_string("alpha", 16))
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.delete(name, really=False)
        self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1078676)
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
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, new_name)
        self.assertIsNotNone(self.activationkey.search_key(new_name))

    @skip_if_bug_open('bugzilla', 1078676)
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
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        description = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, description=new_description)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1089637)
    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_update_activation_key_3(self, env_name):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Environment in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Environment for all variations in [1]
        @Assert: Activation key is updated
        @BZ: 1089637
        """

        name = generate_string("alpha", 8)
        cv_name = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv_name, env_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT,
                                  description=generate_string("alpha", 16))
        self.assertIsNotNone(self.activationkey.search_key(name))
        env_locator = locators["ak.selected_env"]
        selected_env = self.activationkey.get_attribute(name, env_locator)
        self.assertEqual(ENVIRONMENT, selected_env)
        self.activationkey.update(name, content_view=cv_name, env=env_name)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))
        selected_env = self.activationkey.get_attribute(name, env_locator)
        self.assertEqual(env_name, selected_env)

    @attr('ui', 'ak', 'implemented')
    @data(*valid_names_list())
    def test_positive_update_activation_key_4(self, cv2_name):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Content View in an Activation key
        @Steps:
        1. Create Activation key
        2. Update Content View for all variations in [1] and include both
        RH and custom products
        @Assert: Activation key is updated
        @BZ: 1078676
        """

        name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 8)
        cv1_name = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.create_cv(cv1_name, env_name)
        self.create_cv(cv2_name, env_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env_name,
                                  description=generate_string("alpha", 16),
                                  content_view=cv1_name)
        self.assertIsNotNone(self.activationkey.search_key(name))
        cv_locator = locators["ak.selected_cv"]
        selected_cv = self.activationkey.get_attribute(name, cv_locator)
        self.assertEqual(cv1_name, selected_cv)
        self.activationkey.update(name, content_view=cv2_name)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))
        selected_cv = self.activationkey.get_attribute(name, cv_locator)
        self.assertEqual(cv2_name, selected_cv)
        # TODO: Need to check for RH Product too

    @skip_if_bug_open('bugzilla', 1078676)
    @attr('ui', 'ak', 'implemented')
    def test_positive_update_activation_key_5(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Usage limit from Unlimited to a finite number
        @Steps:
        1. Create Activation key
        2. Update Usage limit from Unlimited to a definite number
        @Assert: Activation key is updated
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        limit = "8"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, limit=limit)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1127090)
    @attr('ui', 'ak', 'implemented')
    def test_positive_update_activation_key_6(self):
        """
        @Feature: Activation key - Positive Update
        @Test: Update Usage limit from definite number to Unlimited
        @Steps:
        1. Create Activation key
        2. Update Usage limit from definite number to Unlimited
        @Assert: Activation key is updated
        @BZ: 1127090
        """

        name = generate_string("alpha", 10)
        limit = "6"
        new_limit = "Unlimited"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, limit=limit)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, limit=new_limit)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1083875)
    @data(*invalid_names_list())
    def test_negative_update_activation_key_1(self, new_name):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid name in an activation key
        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @BZ: 1083875
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, new_name)
        invalid = self.products.wait_until_element(common_locators
                                                   ["alert.error"])
        self.assertTrue(invalid)
        self.assertIsNone(self.activationkey.search_key(new_name))

    @skip_if_bug_open('bugzilla', 1110486)
    def test_negative_update_activation_key_2(self):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid Description in an activation key
        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        description = generate_string("alpha", 10)
        new_description = generate_string("alpha", 1001)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT, description=description)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.update(name, description=new_description)
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.error"]))

    @skip_if_bug_open('bugzilla', 1083027)
    @data({u'limit': " "},
          {u'limit': "-1"},
          {u'limit': "text"},
          {u'limit': "0"})
    def test_negative_update_activation_key_3(self, test_data):
        """
        @Feature: Activation key - Negative Update
        @Test: Update invalid Usage Limit in an activation key
        @Steps:
        1. Create Activation key
        2. Update Usage Limit for all variations in [2]
        @Assert: Activation key is not updated.  Appropriate error shown.
        @BZ: 1078676
        """

        name = generate_string("alpha", 10)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(ActivationKey.org_name)
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, ENVIRONMENT)
        self.assertIsNotNone(self.activationkey.search_key(name))
        with self.assertRaises(ValueError) as context:
            self.activationkey.update(name, limit=test_data['limit'])
        self.assertEqual(context.exception.message,
                         "Please update content host limit "
                         "with valid integer value")

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
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
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
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
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_associate_product_1(self):
        """
        @Feature: Activation key - Product
        @Test: Test that RH product can be associated to Activation Keys
        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        @Assert: RH products are successfully associated to Activation key
        @Status: Manual
        @BZ: 1078676
        """
        pass

    def test_associate_product_2(self):
        """
        @Feature: Activation key - Product
        @Test: Test that custom product can be associated to Activation Keys
        @Steps:
        1. Create Activation key
        2. Associate custom product(s) to Activation Key
        @Assert: Custom products are successfully associated to Activation key
        @BZ: 1078676
        """

        name = generate_string("alpha", 8)
        cv_name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 8)
        publish_comment = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name,
                               description=generate_string("alpha", 16))
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        repo_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        publish_version = "Version 1"
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)
        self.navigator.go_to_content_views()
        self.content_views.create(cv_name)
        # Navigating to dashboard is a workaround to
        # refresh repos under selected CV
        self.navigator.go_to_dashboard()
        self.navigator.go_to_content_views()
        self.content_views.add_remove_repos(cv_name, [repo_name])
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.publish(cv_name, publish_comment)
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.promote(cv_name, publish_version, env_name)
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.navigator.go_to_activation_keys()
        self.activationkey.create(name, env_name,
                                  description=generate_string("alpha", 16),
                                  content_view=cv_name)
        self.assertIsNotNone(self.activationkey.search_key(name))
        self.activationkey.associate_product(name, [prd_name])
        self.assertTrue(self.activationkey.wait_until_element
                        (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
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
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
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
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_multiple_activation_keys_to_system(self):
        """
        @Feature: Activation key - System
        @Test: Check if multiple Activation keys can be attached to a system
        @Steps:
        1. Create multiple Activation keys
        2. Attach all the created Activation keys to a System
        @Assert: Multiple Activation keys are attached to a system
        @Status: Manual
        @BZ: 1078676
        """
        pass

    @skip_if_bug_open('bugzilla', 1078676)
    @unittest.skip(NOT_IMPLEMENTED)
    def test_end_to_end_activation_key(self):
        """
        @Feature: Activation key - End to End
        @Test: Create Activation key and provision systems with it
        @Steps:
        1. Create Activation key
        2. Provision systems with Activation key
        @Assert: Systems are successfully provisioned with Activation key
        @Status: Manual
        @BZ: 1078676
        """
        pass
