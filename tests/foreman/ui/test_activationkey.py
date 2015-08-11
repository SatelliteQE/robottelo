# -*- encoding: utf-8 -*-
"""Test class for Activation key UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import client, entities
from robottelo.api import utils
from robottelo.common import manifests
from robottelo.common.constants import (
    DEFAULT_CV,
    DEFAULT_SUBSCRIPTION_NAME,
    ENVIRONMENT,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_TYPE,
)
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.common.helpers import (
    invalid_names_list, valid_data_list, get_server_credentials)
from robottelo.ui.factory import make_activationkey, set_context
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.session import Session
from robottelo.test import UITestCase
from robottelo.vm import VirtualMachine


@ddt
class ActivationKey(UITestCase):
    """Implements Activation key tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name, leading and trailing
    spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size

    """

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        # org label is required for subcription-manager cmd.
        cls.org_label = org_attrs['label']
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']
        cls.base_key_name = entities.ActivationKey(
            organization=cls.org_id
        ).create_json()['name']
        cls.vm_distro = 'rhel65'

        super(ActivationKey, cls).setUpClass()

    def create_sync_custom_repo(
            self, product_name=None, repo_name=None, repo_url=None,
            repo_type=None, org_id=None):
        """Create product/repo, sync it and returns repo_id"""
        product_name = product_name or gen_string('alpha', 8)
        repo_name = repo_name or gen_string('alpha', 8)
        # Creates new product and repository via API's
        product_attrs = entities.Product(
            name=product_name,
            organization=org_id or self.org_id
        ).create_json()
        repo_attrs = entities.Repository(
            name=repo_name,
            url=repo_url or FAKE_1_YUM_REPO,
            content_type=repo_type or REPO_TYPE['yum'],
            product=product_attrs['id'],
        ).create_json()
        repo_id = repo_attrs['id']
        # Sync repository
        entities.Repository(id=repo_id).sync()
        return repo_id

    def enable_sync_redhat_repo(self, rh_repo, org_id=None):
        """Enable the RedHat repo, sync it and returns repo_id"""
        # Enable RH repo and fetch repository_id
        repo_id = utils.enable_rhrepo_and_fetchid(
            basearch=rh_repo['basearch'],
            org_id=org_id or self.org_id,
            product=rh_repo['product'],
            repo=rh_repo['name'],
            reposet=rh_repo['reposet'],
            releasever=rh_repo['releasever'],
        )
        # Sync repository
        entities.Repository(id=repo_id).sync()
        return repo_id

    def cv_publish_promote(self, name, env_name, repo_id, org_id=None):
        """Create, publish and promote CV to selected environment"""
        # Create Life-Cycle content environment
        env_attrs = entities.LifecycleEnvironment(
            name=env_name,
            organization=org_id or self.org_id
        ).create()
        # Create content view(CV)
        content_view = entities.ContentView(
            name=name,
            organization=org_id or self.org_id
        )
        content_view.id = content_view.create_json()['id']

        # Associate YUM repo to created CV
        response = client.put(
            entities.ContentView(id=content_view.id).path(),
            auth=get_server_credentials(),
            verify=False,
            data={u'repository_ids': [repo_id]})
        response.raise_for_status()

        # Publish content view
        content_view.publish()

        # Get the content view version's ID.
        response = client.get(
            entities.ContentViewVersion().path(),
            auth=get_server_credentials(),
            data={u'content_view_id': content_view.id},
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        cv_version = entities.ContentViewVersion(id=results[0]['id'])

        # Promote the content view version.
        cv_version.promote({u'environment_id': env_attrs.id})

    @data(*valid_data_list())
    def test_positive_create_activation_key_1(self, name):
        """@Test: Create Activation key for all variations of Activation
        key name

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key for all valid Activation Key name variation
        in [1] using valid Description, Environment, Content View, Usage limit

        @Assert: Activation key is created

        @BZ: 1078676

        """
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    @data(*valid_data_list())
    def test_positive_create_activation_key_2(self, description):
        """@Test: Create Activation key for all variations of Description

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key for all valid Description variation in [1]
        using valid Name, Environment, Content View and Usage limit

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=description
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_create_activation_key_3(self, env_name):
        """@Test: Create Activation key for all variations of Environments

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View and Usage limit

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        # Helper function to create and sync custom repository
        repo_id = self.create_sync_custom_repo()
        # Helper function to create and promote CV to next environment
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_create_activation_key_4(self, cv_name):
        """@Test: Create Activation key for all variations of Content Views

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key for all valid Content views in [1]
        using valid Name, Description, Environment and Usage limit

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 6)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    @data(*valid_data_list())
    def test_positive_create_activation_key_5(self, hc_name):
        """@Test: Create Activation key for all variations of Host Collections

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key for all valid Host Collections in [1]
        using valid Name, Description, Environment, Content View, Usage limit

        @Assert: Activation key is created

        """
        name = gen_string(str_type='alpha')

        # create Host Collection using API
        host_col = entities.HostCollection(
            organization=self.org_id,
            name=hc_name
        ).create_json()

        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            # add Host Collection
            self.activationkey.add_host_collection(name, host_col['name'])
            result = self.activationkey.find_element(
                common_locators['alert.success'])
            self.assertIsNotNone(result)

            # check added host collection is listed
            self.activationkey.wait_until_element(
                tab_locators['ak.host_collections.list']
            ).click()
            strategy, value = tab_locators['ak.host_collections.add.select']
            host_collection = self.activationkey.wait_until_element(
                (strategy, value % host_col['name']))
            self.assertIsNotNone(host_collection)

    def test_positive_create_activation_key_6(self):
        """@Test: Create Activation key with default Usage limit (Unlimited)

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key with default Usage Limit (Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    def test_positive_create_activation_key_7(self):
        """@Test: Create Activation key with finite Usage limit

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key with finite Usage Limit (Not Unlimited)
        using valid Name, Description, Environment and Content View

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        description = gen_string('alpha', 10)
        limit = '6'
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                limit=limit,
                description=description
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    def test_positive_create_activation_key_8(self):
        """@Test: Create Activation key with minimal input parameters

        @Feature: Activation key - Positive Create

        @Steps:
        1. Create Activation key by entering Activation Key Name alone
        leaving Description, Content View and Usage Limit as default values

        @Assert: Activation key is created

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))

    @data(*invalid_names_list())
    def test_negative_create_activation_key_1(self, name):
        """@Test: Create Activation key with invalid Name

        @Feature: Activation key - Negative Create

        @Steps:
        1. Create Activation key for all invalid Activation Key Names in [2]
        using valid Description, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        """
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            invalid = self.products.wait_until_element(
                common_locators['common_invalid'])
            self.assertIsNotNone(invalid)
            self.assertIsNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1177158)
    def test_negative_create_activation_key_2(self):
        """@Test: Create Activation key with invalid Description

        @Feature: Activation key - Negative Create

        @Steps:
        1. Create Activation key for all invalid Description in [2]
        using valid Name, Environment, Content View, Usage limit

        @Assert: Activation key is not created. Appropriate error shown.

        @BZ: 1177158

        """
        name = gen_string('alpha', 10)
        description = gen_string('alpha', 1001)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=description
            )
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['common_haserror']
                )
            )
            self.assertIsNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1139576)
    @data(*invalid_names_list())
    def test_negative_create_activation_key_3(self, limit):
        """@Test: Create Activation key with invalid Usage Limit

        @Feature: Activation key - Negative Create

        @Steps:
        1. Create Activation key for all invalid Usage Limit in [2]
        using valid Name, Description, Environment, Content View

        @Assert: Activation key is not created. Appropriate error shown.

        @BZ: 1139576

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                limit=limit
            )
            invalid = self.activationkey.wait_until_element(
                locators['ak.invalid_limit']
            )
            self.assertIsNotNone(invalid)
            self.assertIsNone(self.activationkey.search_key(name))

    @data(*valid_data_list())
    def test_positive_delete_activation_key_1(self, name):
        """@Test: Create Activation key and delete it for all variations of
        Activation key name

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Activation Key names in [1]
        using valid Description, Environment, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.delete(name, True)
            self.assertIsNone(self.activationkey.search_key(name))

    @data(*valid_data_list())
    def test_positive_delete_activation_key_2(self, description):
        """@Test: Create Activation key and delete it for all variations of
        Description

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Description in [1]
        using valid Name, Environment, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=description
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.delete(name, True)
            self.assertIsNone(self.activationkey.search_key(name))

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_delete_activation_key_3(self, env_name):
        """@Test: Create Activation key and delete it for all variations of
        Environment

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Environments in [1]
        using valid Name, Description, Content View, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.delete(name, True)
            self.assertIsNone(self.activationkey.search_key(name))

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_delete_activation_key_4(self, cv_name):
        """@Test: Create Activation key and delete it for all variations of
        Content Views

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create Activation key for all valid Content Views in [1]
        using valid Name, Description, Environment, Usage limit
        2. Delete the Activation key

        @Assert: Activation key is deleted

        """
        name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 6)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.delete(name, True)
            self.assertIsNone(self.activationkey.search_key(name))

    def test_positive_delete_activation_key_5(self):
        """@Test: Delete an Activation key which has registered systems

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key
        2. Register systems to it
        3. Delete the Activation key

        @Assert: Activation key is deleted

        """
        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 8)
        product_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo(product_name=product_name)
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.associate_product(name, [product_name])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_cert()
                result = vm.register_contenthost(name, self.org_label)
                self.assertEqual(result.return_code, 0)
                self.activationkey.delete(name, True)
                self.assertIsNone(self.activationkey.search_key(name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1117753)
    def test_positive_delete_activation_key_6(self):
        """@Test: Delete a Content View associated to an Activation Key

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key with a Content View
        2. Delete the Content View

        @Assert: Activation key should not be deleted

        @BZ: 1117753

        """
        name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 6)
        cv_name = gen_string('alpha', 6)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            session.nav.go_to_content_views()
            self.content_views.delete_version(
                cv_name,
                is_affected_comps=True,
                env=ENVIRONMENT,
                cv=DEFAULT_CV
            )
            self.content_views.delete(name, True)
            self.assertIsNone(self.content_views.search(name))
            self.assertIsNotNone(self.activationkey.search_key(name))

    def test_negative_delete_activation_key_1(self):
        """@Test: [UI ONLY] Attempt to delete an Activation Key and cancel it

        @Feature: Activation key - Positive Delete

        @Steps:
        1. Create an Activation key
        2. Attempt to remove an Activation Key
        3. Click Cancel in the confirmation dialog box

        @Assert: Activation key is not deleted

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.delete(name, really=False)
            self.assertIsNotNone(self.activationkey.search_key(name))

    @skip_if_bug_open('bugzilla', 1177330)
    @data(*valid_data_list())
    def test_positive_update_activation_key_1(self, new_name):
        """@Test: Update Activation Key Name in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [1]

        @Assert: Activation key is updated

        @BZ: 1177330

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, new_name)
            self.assertIsNotNone(self.activationkey.search_key(new_name))

    @data(*valid_data_list())
    def test_positive_update_activation_key_2(self, new_description):
        """@Test: Update Description in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [1]

        @Assert: Activation key is updated

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        description = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=description
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, description=new_description)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_update_activation_key_3(self, env_name):
        """@Test: Update Environment in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Environment for all variations in [1]

        @Assert: Activation key is updated

        @BZ: 1089637

        """

        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('alpha', 16)
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            env_locator = locators['ak.selected_env']
            selected_env = self.activationkey.get_attribute(name, env_locator)
            self.assertEqual(ENVIRONMENT, selected_env)
            self.activationkey.update(name, content_view=cv_name, env=env_name)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            selected_env = self.activationkey.get_attribute(name, env_locator)
            self.assertEqual(env_name, selected_env)

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_update_activation_key_4(self, cv2_name):
        """@Test: Update Content View in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update the Content view with another Content view
        which has custom products

        @Assert: Activation key is updated

        """

        name = gen_string('alpha', 8)
        env1_name = gen_string('alpha', 8)
        env2_name = gen_string('alpha', 8)
        cv1_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo1_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv1_name, env1_name, repo1_id)
        repo2_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv2_name, env2_name, repo2_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env1_name,
                description=gen_string('alpha', 16),
                content_view=cv1_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            cv_locator = locators['ak.selected_cv']
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv1_name, selected_cv)
            self.activationkey.update(
                name, content_view=cv2_name, env=env2_name)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv2_name, selected_cv)

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_update_activation_key_with_rh_product(self, cv2_name):
        """@Test: Update Content View in an Activation key

        @Feature: Activation key - Positive Update

        @Steps:

        1. Create an activation key
        2. Update the content view with another content view which has RH
           products

        @Assert: Activation key is updated

        """
        name = gen_string('alpha', 8)
        env1_name = gen_string('alpha', 8)
        env2_name = gen_string('alpha', 8)
        cv1_name = gen_string('alpha', 8)
        rh_repo1 = {
            'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 '
                     'Server RPMs x86_64 6Server'),
            'product': 'Red Hat Enterprise Linux Server',
            'reposet': ('Red Hat Enterprise Virtualization Agents '
                        'for RHEL 6 Server (RPMs)'),
            'basearch': 'x86_64',
            'releasever': '6Server',
        }
        rh_repo2 = {
            'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 '
                     'Server RPMs i386 6Server'),
            'product': 'Red Hat Enterprise Linux Server',
            'reposet': ('Red Hat Enterprise Virtualization Agents '
                        'for RHEL 6 Server (RPMs)'),
            'basearch': 'i386',
            'releasever': '6Server',
        }
        org = entities.Organization().create()
        sub = entities.Subscription()
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload({'organization_id': org.id}, manifest)
        repo1_id = self.enable_sync_redhat_repo(rh_repo1, org.id)
        self.cv_publish_promote(cv1_name, env1_name, repo1_id, org.id)
        repo2_id = self.enable_sync_redhat_repo(rh_repo2, org.id)
        self.cv_publish_promote(cv2_name, env2_name, repo2_id, org.id)

        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=org.name,
                name=name,
                env=env1_name,
                description=gen_string('alpha', 16),
                content_view=cv1_name,
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            cv_locator = locators['ak.selected_cv']
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv1_name, selected_cv)
            self.activationkey.update(
                name, content_view=cv2_name, env=env2_name)
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success']))
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv2_name, selected_cv)

    def test_positive_update_activation_key_5(self):
        """@Test: Update Usage limit from Unlimited to a finite number

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Usage limit from Unlimited to a definite number

        @Assert: Activation key is updated

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        limit = '8'
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, limit=limit)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    @skip_if_bug_open('bugzilla', 1127090)
    def test_positive_update_activation_key_6(self):
        """@Test: Update Usage limit from definite number to Unlimited

        @Feature: Activation key - Positive Update

        @Steps:
        1. Create Activation key
        2. Update Usage limit from definite number to Unlimited

        @Assert: Activation key is updated

        @BZ: 1127090

        """
        name = gen_string('alpha', 10)
        limit = '6'
        new_limit = 'Unlimited'
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                limit=limit
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, limit=new_limit)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    @data(*invalid_names_list())
    def test_negative_update_activation_key_1(self, new_name):
        """@Test: Update invalid name in an activation key

        @Feature: Activation key - Negative Update

        @Steps:
        1. Create Activation key
        2. Update Activation key name for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @BZ: 1083875

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, new_name)
            invalid = self.products.wait_until_element(
                common_locators['alert.error'])
            self.assertIsNotNone(invalid)
            self.assertIsNone(self.activationkey.search_key(new_name))

    @skip_if_bug_open('bugzilla', 1177158)
    def test_negative_update_activation_key_2(self):
        """@Test: Update invalid Description in an activation key

        @Feature: Activation key - Negative Update

        @Steps:
        1. Create Activation key
        2. Update Description for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @BZ: 1177158

        """

        name = gen_string('alpha', 10)
        description = gen_string('alpha', 10)
        new_description = gen_string('alpha', 1001)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT,
                description=description
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, description=new_description)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.error']
                )
            )

    @data(
        {u'limit': ' '},
        {u'limit': '-1'},
        {u'limit': 'text'},
        {u'limit': '0'}
    )
    def test_negative_update_activation_key_3(self, test_data):
        """@Test: Update invalid Usage Limit in an activation key

        @Feature: Activation key - Negative Update

        @Steps:
        1. Create Activation key
        2. Update Usage Limit for all variations in [2]

        @Assert: Activation key is not updated.  Appropriate error shown.

        @BZ: 1078676

        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            with self.assertRaises(ValueError) as context:
                self.activationkey.update(name, limit=test_data['limit'])
            self.assertEqual(
                context.exception.message,
                'Please update content host limit with valid integer value'
            )

    @run_only_on('sat')
    def test_usage_limit(self):
        """@Test: Test that Usage limit actually limits usage

        @Feature: Activation key - Usage limit

        @Steps:
        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Systems to match the Usage Limit
        4. Attempt to register an other system after reaching the Usage Limit

        @Assert: System Registration fails. Appropriate error shown

        """
        name = gen_string('alpha', 10)
        host_limit = '1'
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.update(name, limit=host_limit)
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            with VirtualMachine(distro=self.vm_distro) as vm1:
                with VirtualMachine(distro=self.vm_distro) as vm2:
                    vm1.install_katello_cert()
                    result = vm1.register_contenthost(name, self.org_label)
                    self.assertEqual(result.return_code, 0)
                    vm2.install_katello_cert()
                    result = vm2.register_contenthost(name, self.org_label)
                    self.assertNotEqual(result.return_code, 0)
                    self.assertGreater(len(result.stderr), 0)
                    self.assertIn(
                        'Max Content Hosts ({0}) reached for activation key'
                        .format(host_limit),
                        result.stderr
                    )

    def test_associate_host(self):
        """@Test: Test that hosts can be associated to Activation Keys

        @Feature: Activation key - Host

        @Steps:
        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key

        @Assert: Hosts are successfully associated to Activation key

        @BZ: 1078676

        """
        key_name = gen_string('utf8')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=key_name,
                env=ENVIRONMENT
            )
            self.assertIsNotNone(self.activationkey.search_key(key_name))
            # Creating VM
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_cert()
                vm.register_contenthost(key_name, self.org_label)
                name = self.activationkey.fetch_associated_content_host(
                    key_name)
                self.assertEqual(vm.hostname, name)

    @run_only_on('sat')
    def test_associate_product_1(self):
        """@Test: Test that RH product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key

        @Assert: RH products are successfully associated to Activation key

        """
        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 8)
        rh_repo = {
            'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 '
                     'Server RPMs x86_64 6Server'),
            'product': 'Red Hat Enterprise Linux Server',
            'reposet': ('Red Hat Enterprise Virtualization Agents '
                        'for RHEL 6 Server (RPMs)'),
            'basearch': 'x86_64',
            'releasever': '6Server',
        }
        product_subscription = DEFAULT_SUBSCRIPTION_NAME
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        # Upload manifest
        sub = entities.Subscription()
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload({'organization_id': org_id}, manifest)
        # Helper function to create and promote CV to next environment
        repo_id = self.enable_sync_redhat_repo(rh_repo, org_id=org_id)
        self.cv_publish_promote(cv_name, env_name, repo_id, org_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=org_attrs['name'],
                name=name,
                env=env_name,
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.associate_product(name, [product_subscription])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    @run_only_on('sat')
    def test_associate_product_2(self):
        """@Test: Test that custom product can be associated to Activation Keys

        @Feature: Activation key - Product

        @Steps:
        1. Create Activation key
        2. Associate custom product(s) to Activation Key

        @Assert: Custom products are successfully associated to Activation key

        @BZ: 1078676

        """
        name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        env_name = gen_string('alpha', 8)
        product_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo(product_name=product_name)
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.org_name,
                name=name,
                env=env_name,
                description=gen_string('alpha', 16),
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.associate_product(name, [product_name])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    @run_only_on('sat')
    def test_associate_product_3(self):
        """@Test: Test that RH/Custom product can be associated to Activation
        keys

        @Feature: Activation key - Product

        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @Assert: RH/Custom product is successfully associated to Activation key

        """
        name = gen_string('alpha', 8)
        rh_repo = {
            'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 '
                     'Server RPMs x86_64 6Server'),
            'product': 'Red Hat Enterprise Linux Server',
            'reposet': ('Red Hat Enterprise Virtualization Agents '
                        'for RHEL 6 Server (RPMs)'),
            'basearch': 'x86_64',
            'releasever': '6Server',
        }
        product_subscription = DEFAULT_SUBSCRIPTION_NAME
        custom_product_name = gen_string('alpha', 8)
        repo_name = gen_string('alpha', 8)
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        # Creates new product and repository via API's
        product_attrs = entities.Product(
            name=custom_product_name,
            organization=org_id
        ).create_json()
        repo_attrs = entities.Repository(
            name=repo_name,
            url=FAKE_1_YUM_REPO,
            content_type=REPO_TYPE['yum'],
            product=product_attrs['id'],
        ).create_json()
        custom_repo_id = repo_attrs['id']
        # Upload manifest
        sub = entities.Subscription()
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload({'organization_id': org_id}, manifest)
        # Enable RH repo and fetch repository_id
        rhel_repo_id = utils.enable_rhrepo_and_fetchid(
            basearch=rh_repo['basearch'],
            org_id=org_id,
            product=rh_repo['product'],
            repo=rh_repo['name'],
            reposet=rh_repo['reposet'],
            releasever=rh_repo['releasever'],
        )
        # Sync repository
        for repo_id in [rhel_repo_id, custom_repo_id]:
            entities.Repository(id=repo_id).sync()
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=org_attrs['name'],
                name=name,
                env=ENVIRONMENT,
                content_view=DEFAULT_CV
            )
            self.assertIsNotNone(self.activationkey.search_key(name))
            self.activationkey.associate_product(
                name, [product_subscription, custom_product_name])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )

    def test_delete_manifest(self):
        """@Test: Check if deleting a manifest removes it from Activation key

        @Feature: Activation key - Manifest

        @Steps:
        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest

        @Assert: Deleting a manifest removes it from the Activation key

        """
        # Upload manifest
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload({'organization_id': org.id}, manifest)
        # Create activation key
        activation_key = entities.ActivationKey(
            organization=org.id,
        ).create()
        # Associate a manifest to the activation key
        for subs in sub.search():
            if subs.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': subs.id,
                })
                break
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            # Verify subscription is assigned to activation key
            self.navigator.go_to_activation_keys()
            self.assertIsNotNone(
                self.activationkey.search_key_subscriptions(
                    activation_key.name, DEFAULT_SUBSCRIPTION_NAME
                )
            )
            # Delete the manifest
            self.navigator.go_to_red_hat_subscriptions()
            self.subscriptions.delete()
            self.assertIsNotNone(
                self.subscriptions.wait_until_element(
                    common_locators['alert.success']
                )
            )
            # Verify the subscription was removed from the activation key
            self.navigator.go_to_activation_keys()
            self.assertIsNone(
                self.activationkey.search_key_subscriptions(
                    activation_key.name, DEFAULT_SUBSCRIPTION_NAME
                )
            )

    @run_only_on('sat')
    def test_multiple_activation_keys_to_system(self):
        """@Test: Check if multiple Activation keys can be attached to a system

        @Feature: Activation key - System

        @Steps:
        1. Create multiple Activation keys
        2. Attach all the created Activation keys to a System

        @Assert: Multiple Activation keys are attached to a system

        """
        key_1_name = gen_string('alpha', 8)
        key_2_name = gen_string('alpha', 8)
        cv_1_name = gen_string('alpha', 8)
        cv_2_name = gen_string('alpha', 8)
        env_1_name = gen_string('alpha', 8)
        env_2_name = gen_string('alpha', 8)
        product_1_name = gen_string('alpha', 8)
        product_2_name = gen_string('alpha', 8)
        # Helper function to create and promote CV to next environment
        repo_1_id = self.create_sync_custom_repo(product_name=product_1_name)
        self.cv_publish_promote(cv_1_name, env_1_name, repo_1_id)
        repo_2_id = self.create_sync_custom_repo(
            product_name=product_2_name, repo_url=FAKE_2_YUM_REPO)
        self.cv_publish_promote(cv_2_name, env_2_name, repo_2_id)
        with Session(self.browser) as session:
            # Create activation_key_1
            make_activationkey(
                session,
                org=self.org_name,
                name=key_1_name,
                env=env_1_name,
                description=gen_string('alpha', 16),
                content_view=cv_1_name
            )
            self.assertIsNotNone(self.activationkey.search_key(key_1_name))
            self.activationkey.associate_product(key_1_name, [product_1_name])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            # Create activation_key_2
            make_activationkey(
                session,
                org=self.org_name,
                name=key_2_name,
                env=env_2_name,
                description=gen_string('alpha', 16),
                content_view=cv_2_name
            )
            self.assertIsNotNone(self.activationkey.search_key(key_2_name))
            self.activationkey.associate_product(key_2_name, [product_2_name])
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators['alert.success']
                )
            )
            # Create VM
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_cert()
                result = vm.register_contenthost(
                    '{0},{1}'.format(key_1_name, key_2_name),
                    self.org_label
                )
                self.assertEqual(result.return_code, 0)
                # Assert the content-host association with activation-key
                for key_name in [key_1_name, key_2_name]:
                    name = self.activationkey.fetch_associated_content_host(
                        key_name)
                    self.assertEqual(vm.hostname, name)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1078676)
    @stubbed()
    def test_end_to_end_activation_key(self):
        """@Test: Create Activation key and provision content-host with it

        Associate activation-key with host-group to auto-register the
        content-host during provisioning itself.

        @Feature: Activation key - End to End

        @Steps:
        1. Create Activation key
        2. Associate it to host-group
        3. Provision content-host with same Activation key

        @Assert: Content-host should be successfully provisioned and registered
        with Activation key

        @Status: Manual

        @BZ: 1078676

        """
        pass

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_positive_copy_activation_key(self, new_name):
        """@Test: Create Activation key and copy it

        @Feature: Activation key - Positive Copy

        @Steps:
        1. Create Activation key
        2. Copy the Activation key with a valid name

        @Assert: Activation Key copy exists

        """
        with Session(self.browser) as session:
            set_context(session, org=self.org_name)
            self.navigator.go_to_activation_keys()
            self.assertIsNotNone(
                self.activationkey.search_key(self.base_key_name))
            self.activationkey.copy(self.base_key_name, new_name)
            self.assertIsNotNone(self.activationkey.search_key(new_name))

    @run_only_on('sat')
    @data(*invalid_names_list())
    def test_negative_copy_activation_key(self, new_name):
        """@Test: Create Activation key and fail copying it

        @Feature: Activation key -Negative Copy

        @Steps:
        1. Create Activation key
        2. Copy the Activation key with an invalid name

        @Assert: Activation Key copy does not exist

        """
        with Session(self.browser) as session:
            set_context(session, org=self.org_name)
            self.navigator.go_to_activation_keys()
            self.assertIsNotNone(
                self.activationkey.search_key(self.base_key_name))
            self.activationkey.copy(self.base_key_name, new_name)
            self.assertIsNone(self.activationkey.search_key(new_name))
