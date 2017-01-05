# -*- encoding: utf-8 -*-
"""Test class for Activation key UI

@Requirement: Activationkey

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

import random
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.cli.factory import (
    activationkey_add_subscription_to_repo,
    make_activation_key,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    setup_org_for_a_rh_repo,
)
from robottelo.constants import (
    DEFAULT_CV,
    DEFAULT_SUBSCRIPTION_NAME,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    ENVIRONMENT,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    PRDS,
    REPOSET,
    REPOS,
    REPO_TYPE,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_activationkey, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class ActivationKeyTestCase(UITestCase):
    """Implements Activation key tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(ActivationKeyTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.base_key_name = entities.ActivationKey(
            organization=cls.organization
        ).create().name
        cls.vm_distro = DISTRO_RHEL6

    # pylint: disable=too-many-arguments
    def create_sync_custom_repo(self, product_name=None, repo_name=None,
                                repo_url=None, repo_type=None, org_id=None):
        """Create product/repo, sync it and returns repo_id"""
        product_name = product_name or gen_string('alpha')
        repo_name = repo_name or gen_string('alpha')
        # Creates new product and repository via API's
        product = entities.Product(
            name=product_name,
            organization=org_id or self.organization
        ).create()
        repo = entities.Repository(
            name=repo_name,
            url=repo_url or FAKE_1_YUM_REPO,
            content_type=repo_type or REPO_TYPE['yum'],
            product=product,
        ).create()
        # Sync repository
        entities.Repository(id=repo.id).sync()
        return repo.id

    def enable_sync_redhat_repo(self, rh_repo, org_id=None):
        """Enable the RedHat repo, sync it and returns repo_id"""
        # Enable RH repo and fetch repository_id
        repo_id = enable_rhrepo_and_fetchid(
            basearch=rh_repo['basearch'],
            org_id=org_id or self.organization.id,
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
        lce = entities.LifecycleEnvironment(
            name=env_name,
            organization=org_id or self.organization
        ).create()

        # Create content view(CV)
        content_view = entities.ContentView(
            name=name,
            organization=org_id or self.organization
        ).create()

        # Associate YUM repo to created CV
        content_view.repository = [entities.Repository(id=repo_id)]
        content_view = content_view.update(['repository'])

        # Publish content view
        content_view.publish()

        # Promote the content view version.
        promote(content_view.read().version[0], lce.id)

    @tier1
    def test_positive_create_with_name(self):
        """Create Activation key for all variations of Activation key
        name

        @id: 091f1034-9850-4004-a0ca-d398d1626a5e

        @Assert: Activation key is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                    )
                    self.assertIsNotNone(self.activationkey.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Activation key with description

        @id: 4c8f4dca-723f-4dae-a8df-4e00a7fc7d95

        @Assert: Activation key is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('utf8'),
            )
            self.assertIsNotNone(self.activationkey.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_envs(self):
        """Create Activation key for all variations of Environments

        @id: f75e994a-6da1-40a3-9685-f8387388b3f0

        @Assert: Activation key is created

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for env_name in valid_data_list():
                with self.subTest(env_name):
                    name = gen_string('alpha')
                    cv_name = gen_string('alpha')
                    # Helper function to create and sync custom repository
                    repo_id = self.create_sync_custom_repo()
                    # Helper function to create and promote CV to next env
                    self.cv_publish_promote(cv_name, env_name, repo_id)
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=env_name,
                        content_view=cv_name,
                    )
                    self.assertIsNotNone(self.activationkey.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_cv(self):
        """Create Activation key for all variations of Content Views

        @id: 2ad000f1-6c80-46aa-a61b-9ea62cefe91b

        @Assert: Activation key is created

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for cv_name in valid_data_list():
                with self.subTest(cv_name):
                    name = gen_string('alpha')
                    env_name = gen_string('alpha')
                    # Helper function to create and promote CV to next env
                    repo_id = self.create_sync_custom_repo()
                    self.cv_publish_promote(cv_name, env_name, repo_id)
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=env_name,
                        content_view=cv_name,
                    )
                    self.assertIsNotNone(self.activationkey.search(name))

    @tier2
    def test_positive_create_with_host_collection(self):
        """Create Activation key with Host Collection

        @id: 0e4ad2b4-47a7-4087-828f-2b0535a97b69

        @Assert: Activation key is created

        @CaseLevel: Integration
        """
        name = gen_string(str_type='alpha')
        # create Host Collection using API
        host_col = entities.HostCollection(
            organization=self.organization,
            name=gen_string(str_type='utf8'),
        ).create()

        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            # add Host Collection
            self.activationkey.add_host_collection(name, host_col.name)
            self.assertIsNotNone(self.activationkey.find_element(
                common_locators['alert.success_sub_form']))

            # check added host collection is listed
            self.activationkey.click(tab_locators['ak.host_collections.list'])
            host_collection = self.activationkey.wait_until_element(
                tab_locators['ak.host_collections.add.select'] % host_col.name)
            self.assertIsNotNone(host_collection)

    @tier2
    def test_positive_add_host_collection_non_admin(self):
        """Test that host collection can be associated to Activation Keys
        by non-admin user.

        @id: 417f0b36-fd49-4414-87ab-6f72a09696f2

        @Assert: Activation key is created, added host collection is listed

        @CaseLevel: Integration
        """
        ak_name = gen_string('alpha')
        # create Host Collection using API
        hc = entities.HostCollection(
            organization=self.organization,
            name=gen_string('alpha'),
        ).create()
        # Create non-admin user with specified permissions
        role = entities.Role().create()
        for res_type in ['Katello::ActivationKey', 'Katello::HostCollection']:
            permission = entities.Permission(resource_type=res_type).search()
            entities.Filter(permission=permission, role=role).create()
        # Add 'Viewer' role to be able to read default environment and
        # content view while creating AK
        role2 = entities.Role().search(query={'search': 'name="Viewer"'})[0]
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            role=[role, role2],
            password=password,
            organization=[self.organization],
        ).create()
        with Session(
                self.browser, user=user.login, password=password) as session:
            make_activationkey(session, name=ak_name, env=ENVIRONMENT)
            self.assertIsNotNone(self.activationkey.search(ak_name))
            # add Host Collection
            self.activationkey.add_host_collection(ak_name, hc.name)
            self.assertIsNotNone(self.activationkey.find_element(
                common_locators['alert.success_sub_form']))
            # check added host collection is listed
            self.activationkey.click(tab_locators['ak.host_collections.list'])
            host_collection = self.activationkey.wait_until_element(
                tab_locators['ak.host_collections.add.select'] % hc.name)
            self.assertIsNotNone(host_collection)

    @tier2
    def test_positive_remove_host_collection_non_admin(self):
        """Test that host collection can be removed from Activation Keys
        by non-admin user.

        @id: 187456ec-5690-4524-9701-8bdb74c7912a

        @Assert: Activation key is created, removed host collection
        is not listed

        @CaseLevel: Integration
        """
        ak_name = gen_string('alpha')
        # create Host Collection using API
        hc = entities.HostCollection(
            organization=self.organization,
            name=gen_string('alpha'),
        ).create()
        # Create non-admin user with specified permissions
        role = entities.Role().create()
        for res_type in ['Katello::ActivationKey', 'Katello::HostCollection']:
            permission = entities.Permission(resource_type=res_type).search()
            entities.Filter(permission=permission, role=role).create()
        # Add 'Viewer' role to be able to read default environment and
        # content view while creating AK
        role2 = entities.Role().search(query={'search': 'name="Viewer"'})[0]
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            role=[role, role2],
            password=password,
            organization=[self.organization],
        ).create()
        with Session(
                self.browser, user=user.login, password=password) as session:
            make_activationkey(session, name=ak_name, env=ENVIRONMENT)
            self.assertIsNotNone(self.activationkey.search(ak_name))
            # add Host Collection
            self.activationkey.add_host_collection(ak_name, hc.name)
            self.assertIsNotNone(self.activationkey.find_element(
                common_locators['alert.success_sub_form']))
            # check added host collection is listed
            self.activationkey.click(tab_locators['ak.host_collections.list'])
            host_collection = self.activationkey.wait_until_element(
                tab_locators['ak.host_collections.add.select'] % hc.name)
            self.assertIsNotNone(host_collection)
            # remove Host Collection
            self.activationkey.remove_host_collection(ak_name, hc.name)
            self.assertIsNotNone(self.activationkey.find_element(
                common_locators['alert.success_sub_form']))
            # check added host collection is not listed
            self.activationkey.click(tab_locators['ak.host_collections.list'])
            host_collection = self.activationkey.wait_until_element(
                tab_locators['ak.host_collections.add.select'] % hc.name)
            self.assertIsNone(host_collection)

    @tier1
    def test_positive_create_with_usage_limit(self):
        """Create Activation key with finite Usage limit

        @id: cd45363e-8a79-4aa4-be97-885aea9434c9

        @Assert: Activation key is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                limit='6',
            )
            self.assertIsNotNone(self.activationkey.search(name))

    @tier2
    def test_negative_create_with_invalid_name(self):
        """Create Activation key with invalid Name

        @id: 143ca57d-89ff-45e0-99cf-4d4033ea3690

        @Assert: Activation key is not created. Appropriate error shown.

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                    )
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['common_invalid']))
                    self.assertIsNone(self.activationkey.search(name))

    @tier2
    def test_negative_create_with_invalid_limit(self):
        """Create Activation key with invalid Usage Limit. Both with too
        long numbers and using letters.

        @id: 71ecf5b2-ce4f-41b0-b30d-45f89713f8c1

        @Assert: Activation key is not created. Appropriate error shown.

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for limit in invalid_names_list():
                with self.subTest(limit):
                    name = gen_string('alpha')
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                        limit=limit,
                    )
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['invalid_limit']))
                    self.assertIsNone(self.activationkey.search(name))

    @tier1
    def test_positive_delete(self):
        """Create Activation key and delete it for all variations of
        Activation key name

        @id: 113e4c1e-cf4d-4c6a-88c9-766db8271933

        @Assert: Activation key is deleted
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                        description=gen_string('utf8'),
                    )
                    self.assertIsNotNone(self.activationkey.search(name))
                    self.activationkey.delete(name)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_with_env(self):
        """Create Activation key with environment and delete it

        @id: b6019881-3d6e-4b75-89f5-1b62aff3b1ca

        @Assert: Activation key is deleted

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('utf8')
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=env_name,
                content_view=cv_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.delete(name)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_with_cv(self):
        """Create Activation key with content view and delete it

        @id: 7e40e1ed-8314-406b-9451-05f64806a6e6

        @Assert: Activation key is deleted

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        cv_name = gen_string('utf8')
        env_name = gen_string('alpha')
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=env_name,
                content_view=cv_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.delete(name)

    @skip_if_not_set('clients')
    @tier3
    def test_positive_delete_with_system(self):
        """Delete an Activation key which has registered systems

        @id: 86cd070e-cf46-4bb1-b555-e7cb42e4dc9f

        @Steps:
        1. Create an Activation key
        2. Register systems to it
        3. Delete the Activation key

        @Assert: Activation key is deleted

        @CaseLevel: System
        """
        name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        product_name = gen_string('alpha')
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo(product_name=product_name)
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=env_name,
                content_view=cv_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.associate_product(name, [product_name])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_ca()
                result = vm.register_contenthost(self.organization.label, name)
                self.assertEqual(result.return_code, 0)
                self.activationkey.delete(name)

    @tier1
    def test_negative_delete(self):
        """[UI ONLY] Attempt to delete an Activation Key and cancel it

        @id: 07a17b98-b756-405c-b0c2-516f2a16aff1

        @Steps:
        1. Create an Activation key
        2. Attempt to remove an Activation Key
        3. Click Cancel in the confirmation dialog box

        @Assert: Activation key is not deleted
        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.delete(name, really=False)

    @tier1
    def test_positive_update_name(self):
        """Update Activation Key Name in an Activation key

        @id: 81d74424-893d-46c4-a20c-c20c85d4e898

        @Assert: Activation key is updated
        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.activationkey.update(name, new_name)
                    self.assertIsNotNone(
                        self.activationkey.search(new_name))
                    name = new_name

    @tier1
    def test_positive_update_description(self):
        """Update Description in an Activation key

        @id: 24988466-af1d-4dcd-80b7-9c7d317fb805

        @Assert: Activation key is updated
        """
        name = gen_string('alpha')
        description = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                description=description,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.activationkey.update(name, description=new_desc)
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_update_env(self):
        """Update Environment in an Activation key

        @id: 895cda6a-bb1e-4b94-a858-95f0be78a17b

        @Assert: Activation key is updated

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('utf8')
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            env_locator = locators['ak.selected_env']
            selected_env = self.activationkey.get_attribute(name, env_locator)
            self.assertEqual(ENVIRONMENT, selected_env)
            self.activationkey.update(name, content_view=cv_name, env=env_name)
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            selected_env = self.activationkey.get_attribute(name, env_locator)
            self.assertEqual(env_name, selected_env)

    @run_only_on('sat')
    @tier2
    def test_positive_update_cv(self):
        """Update Content View in an Activation key

        @id: 68880ca6-acb9-4a16-aaa0-ced680126732

        @Steps:
        1. Create Activation key
        2. Update the Content view with another Content view which has custom
        products

        @Assert: Activation key is updated

        @CaseLevel: Integration
        """
        # Pick one of the valid data list items - data driven tests is not
        # necessary for this test
        cv2_name = random.choice(valid_data_list())
        name = gen_string('alpha')
        env1_name = gen_string('alpha')
        env2_name = gen_string('alpha')
        cv1_name = gen_string('alpha')
        # Helper function to create and promote CV to next environment
        repo1_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv1_name, env1_name, repo1_id)
        repo2_id = self.create_sync_custom_repo()
        self.cv_publish_promote(cv2_name, env2_name, repo2_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=env1_name,
                content_view=cv1_name
            )
            self.assertIsNotNone(self.activationkey.search(name))
            cv_locator = locators['ak.selected_cv']
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv1_name, selected_cv)
            self.activationkey.update(
                name, content_view=cv2_name, env=env2_name)
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv2_name, selected_cv)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_update_rh_product(self):
        """Update Content View in an Activation key

        @id: 9b0ac209-45de-4cc4-97e8-e191f3f37239

        @Steps:

        1. Create an activation key
        2. Update the content view with another content view which has RH
           products

        @Assert: Activation key is updated

        @CaseLevel: Integration
        """
        # Pick one of the valid data list items - data driven tests is not
        # necessary for this test
        cv2_name = random.choice(valid_data_list())
        name = gen_string('alpha')
        env1_name = gen_string('alpha')
        env2_name = gen_string('alpha')
        cv1_name = gen_string('alpha')
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
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
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
                content_view=cv1_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            cv_locator = locators['ak.selected_cv']
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv1_name, selected_cv)
            self.activationkey.update(
                name, content_view=cv2_name, env=env2_name)
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            selected_cv = self.activationkey.get_attribute(name, cv_locator)
            self.assertEqual(cv2_name, selected_cv)

    @tier1
    def test_positive_update_limit(self):
        """Update Usage limit from Unlimited to a finite number

        @id: e6ef8dbe-dfb6-4226-8253-ff2e24cabe12

        @Assert: Activation key is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.update(name, limit='8')
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @tier1
    def test_positive_update_limit_to_unlimited(self):
        """Update Usage limit from definite number to Unlimited

        @id: 2585ac91-baf0-43de-ba6e-862415402e62

        @Assert: Activation key is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                limit='6',
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.update(name, limit='Unlimited')
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @tier1
    def test_negative_update_name(self):
        """Update invalid name in an activation key

        @id: 6eb0f747-cd4d-421d-b11e-b8917bb0cec6

        @Assert: Activation key is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.activationkey.update(name, new_name)
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['alert.error_sub_form']))
                    self.assertIsNone(self.activationkey.search(new_name))

    @tier1
    def test_negative_update_limit(self):
        """Update invalid Usage Limit in an activation key

        @id: d42d8b6a-d3f4-4baa-be20-127f52f2313e

        @Assert: Activation key is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for limit in ' ', -1, 'text', '0':
                with self.subTest(limit):
                    with self.assertRaises(ValueError) as context:
                        self.activationkey.update(name, limit=limit)
                    self.assertEqual(
                        context.exception.message,
                        'Please update content host limit with valid ' +
                        'integer value'
                    )

    @run_only_on('sat')
    @skip_if_not_set('clients')
    @tier3
    def test_negative_usage_limit(self):
        """Test that Usage limit actually limits usage

        @id: 9fe2d661-66f8-46a4-ae3f-0a9329494bdd

        @Steps:
        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Systems to match the Usage Limit
        4. Attempt to register an other system after reaching the Usage Limit

        @Assert: System Registration fails. Appropriate error shown

        @CaseLevel: System
        """
        name = gen_string('alpha')
        host_limit = '1'
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.update(name, limit=host_limit)
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            with VirtualMachine(distro=self.vm_distro) as vm1:
                with VirtualMachine(distro=self.vm_distro) as vm2:
                    vm1.install_katello_ca()
                    result = vm1.register_contenthost(
                        self.organization.label, name)
                    self.assertEqual(result.return_code, 0)
                    vm2.install_katello_ca()
                    result = vm2.register_contenthost(
                        self.organization.label, name)
                    self.assertNotEqual(result.return_code, 0)
                    self.assertGreater(len(result.stderr), 0)
                    self.assertIn(
                        'Max Hosts ({0}) reached for activation key'
                        .format(host_limit),
                        result.stderr
                    )

    @skip_if_not_set('clients')
    @tier3
    def test_positive_add_host(self):
        """Test that hosts can be associated to Activation Keys

        @id: 886e9ea5-d917-40e0-a3b1-41254c4bf5bf

        @Steps:
        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key

        @Assert: Hosts are successfully associated to Activation key

        @CaseLevel: System
        """
        key_name = gen_string('utf8')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=key_name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(key_name))
            # Creating VM
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_ca()
                vm.register_contenthost(self.organization.label, key_name)
                name = self.activationkey.fetch_associated_content_host(
                    key_name)
                self.assertEqual(vm.hostname, name)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_rh_product(self):
        """Test that RH product can be associated to Activation Keys

        @id: d805341b-6d2f-4e16-8cb4-902de00b9a6c

        @Assert: RH products are successfully associated to Activation key

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
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
        org = entities.Organization().create()
        # Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        # Helper function to create and promote CV to next environment
        repo_id = self.enable_sync_redhat_repo(rh_repo, org_id=org.id)
        self.cv_publish_promote(cv_name, env_name, repo_id, org.id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=org.name,
                name=name,
                env=env_name,
                content_view=cv_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.associate_product(name, [product_subscription])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_custom_product(self):
        """Test that custom product can be associated to Activation Keys

        @id: e66db2bf-517a-46ff-ba23-9f9744bef884

        @Assert: Custom products are successfully associated to Activation key

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        product_name = gen_string('alpha')
        # Helper function to create and promote CV to next environment
        repo_id = self.create_sync_custom_repo(product_name=product_name)
        self.cv_publish_promote(cv_name, env_name, repo_id)
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=env_name,
                content_view=cv_name,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.associate_product(name, [product_name])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_rh_and_custom_products(self):
        """Test that RH/Custom product can be associated to Activation
        keys

        @id: 3d8876fa-1412-47ca-a7a4-bce2e8baf3bc

        @Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

        @Assert: RH/Custom product is successfully associated to Activation key

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
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
        custom_product_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        # Create new org to import manifest
        org = entities.Organization().create()
        # Creates new product and repository via API's
        product = entities.Product(
            name=custom_product_name,
            organization=org,
        ).create()
        repo = entities.Repository(
            name=repo_name,
            url=FAKE_1_YUM_REPO,
            content_type=REPO_TYPE['yum'],
            product=product,
        ).create()
        # Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        # Enable RH repo and fetch repository_id
        rhel_repo_id = enable_rhrepo_and_fetchid(
            basearch=rh_repo['basearch'],
            org_id=org.id,
            product=rh_repo['product'],
            repo=rh_repo['name'],
            reposet=rh_repo['reposet'],
            releasever=rh_repo['releasever'],
        )
        # Sync repository
        for repo_id in [rhel_repo_id, repo.id]:
            entities.Repository(id=repo_id).sync()
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=org.name,
                name=name,
                env=ENVIRONMENT,
                content_view=DEFAULT_CV,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.associate_product(
                name, [product_subscription, custom_product_name])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_delete_manifest(self):
        """Check if deleting a manifest removes it from Activation key

        @id: 512d8e41-b937-451e-a9c6-840457d3d7d4

        @Steps:
        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest

        @Assert: Deleting a manifest removes it from the Activation key

        @CaseLevel: Integration
        """
        # Upload manifest
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        # Create activation key
        activation_key = entities.ActivationKey(
            organization=org,
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
            self.assertIsNotNone(
                self.activationkey.search_key_subscriptions(
                    activation_key.name, DEFAULT_SUBSCRIPTION_NAME
                )
            )
            # Delete the manifest
            self.navigator.go_to_red_hat_subscriptions()
            self.subscriptions.delete()
            self.assertIsNotNone(self.subscriptions.wait_until_element(
                common_locators['alert.success'], timeout=180))
            # Verify the subscription was removed from the activation key
            self.assertIsNone(
                self.activationkey.search_key_subscriptions(
                    activation_key.name, DEFAULT_SUBSCRIPTION_NAME
                )
            )

    @run_only_on('sat')
    @skip_if_not_set('clients')
    @tier3
    def test_positive_add_multiple_aks_to_system(self):
        """Check if multiple Activation keys can be attached to a system

        @id: 4d6b6b69-9d63-4180-af2e-a5d908f8adb7

        @Assert: Multiple Activation keys are attached to a system

        @CaseLevel: System
        """
        key_1_name = gen_string('alpha')
        key_2_name = gen_string('alpha')
        cv_1_name = gen_string('alpha')
        cv_2_name = gen_string('alpha')
        env_1_name = gen_string('alpha')
        env_2_name = gen_string('alpha')
        product_1_name = gen_string('alpha')
        product_2_name = gen_string('alpha')
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
                org=self.organization.name,
                name=key_1_name,
                env=env_1_name,
                content_view=cv_1_name,
            )
            self.assertIsNotNone(self.activationkey.search(key_1_name))
            self.activationkey.associate_product(key_1_name, [product_1_name])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Create activation_key_2
            make_activationkey(
                session,
                org=self.organization.name,
                name=key_2_name,
                env=env_2_name,
                content_view=cv_2_name,
            )
            self.assertIsNotNone(self.activationkey.search(key_2_name))
            self.activationkey.associate_product(key_2_name, [product_2_name])
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Create VM
            with VirtualMachine(distro=self.vm_distro) as vm:
                vm.install_katello_ca()
                result = vm.register_contenthost(
                    self.organization.label,
                    '{0},{1}'.format(key_1_name, key_2_name),
                )
                self.assertEqual(result.return_code, 0)
                # Assert the content-host association with activation-key
                for key_name in [key_1_name, key_2_name]:
                    name = self.activationkey.fetch_associated_content_host(
                        key_name)
                    self.assertEqual(vm.hostname, name)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_end_to_end(self):
        """Create Activation key and provision content-host with it

        Associate activation-key with host-group to auto-register the
        content-host during provisioning itself.

        @id: 1dc0079d-f41f-454b-9554-1235cabd1a4c

        @Steps:
        1. Create Activation key
        2. Associate it to host-group
        3. Provision content-host with same Activation key

        @Assert: Content-host should be successfully provisioned and registered
        with Activation key

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @tier1
    def test_positive_copy(self):
        """Create Activation key and copy it

        @id: f43d9ecf-f8ec-49cc-bd12-be7cdb3bf07c

        @Assert: Activation Key copy exists
        """
        with Session(self.browser) as session:
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    set_context(session, org=self.organization.name)
                    self.assertIsNotNone(
                        self.activationkey.search(self.base_key_name))
                    self.activationkey.copy(self.base_key_name, new_name)
                    self.assertIsNotNone(
                        self.activationkey.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_negative_copy(self):
        """Create Activation key and fail copying it

        @id: 117af9a8-e669-46cb-8a54-071087d0d082

        @Assert: Activation Key copy does not exist
        """
        with Session(self.browser) as session:
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    set_context(session, org=self.organization.name)
                    self.assertIsNotNone(
                        self.activationkey.search(self.base_key_name))
                    self.activationkey.copy(self.base_key_name, new_name)
                    self.assertIsNone(self.activationkey.search(new_name))

    @run_in_one_thread
    @tier3
    def test_positive_list_hosts(self):
        """Verify only hosts registered by specific activation key are listed
        on Activation Key -> Associations -> Content Hosts page

        @id: 9364bfcc-ef69-4183-9ca8-e2904b3f4068

        @Steps:
        1. Create 2 activation keys
        2. Register 2 hosts, one for each activation key

        @Assert: Activation Key -> Associations -> Content Hosts page should
        show only hosts registered via the key

        @BZ: 1372826
        """
        org = make_org()
        env = make_lifecycle_environment({'organization-id': org['id']})
        content_view = make_content_view({'organization-id': org['id']})
        activation_key = make_activation_key({
            'lifecycle-environment-id': env['id'],
            'organization-id': org['id'],
        })
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': env['id'],
            'activationkey-id': activation_key['id'],
        })
        another_ak = make_activation_key({
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': env['id'],
            'organization-id': org['id'],
        })
        activationkey_add_subscription_to_repo({
            'activationkey-id': another_ak['id'],
            'organization-id': org['id'],
            'subscription': DEFAULT_SUBSCRIPTION_NAME,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client1, VirtualMachine(
                distro=DISTRO_RHEL7) as client2:
            client1.install_katello_ca()
            client2.install_katello_ca()
            result = client1.register_contenthost(
                org['label'], activation_key['name'])
            self.assertEqual(result.return_code, 0)
            result = client2.register_contenthost(
                org['label'], another_ak['name'])
            self.assertEqual(result.return_code, 0)
            with Session(self.browser) as session:
                set_context(session, org=org['name'])
                self.assertIsNotNone(
                    self.activationkey.search_host(
                        activation_key['name'], client1.hostname)
                )
                self.assertIsNone(
                    self.activationkey.search_host(
                        activation_key['name'], client2.hostname)
                )
                self.assertIsNotNone(
                    self.activationkey.search_host(
                        another_ak['name'], client2.hostname)
                )
                self.assertIsNone(
                    self.activationkey.search_host(
                        another_ak['name'], client1.hostname)
                )
