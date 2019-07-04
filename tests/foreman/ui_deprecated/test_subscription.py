"""Test class for Subscriptions/Manifests UI

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    create_role_permissions,
    enable_rhrepo_and_fetchid,
    promote,
)
from robottelo.cli.factory import (
    make_virt_who_config,
    virt_who_hypervisor_config,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
    PRDS,
    REPOS,
    REPOSET,
    VIRT_WHO_HYPERVISOR_TYPES,
    VDC_SUBSCRIPTION_NAME,
)

from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade,
)

from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def set_session_org(cls):
        cls.session_org = entities.Organization().create()

    @skip_if_not_set('fake_manifest')
    @tier1
    @upgrade
    def test_positive_upload_and_delete(self):
        """Upload a manifest with minimal input parameters and delete it

        :id: 58e549b0-1ba3-421d-8075-dcf65d07510b

        :expectedresults: Manifest is uploaded and deleted successfully

        :CaseImportance: Critical
        """
        with Session(self):
            # Step 1: Attempt to upload a manifest
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(self.subscriptions.wait_until_element_exists(
                locators['subs.import_history.imported']))
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
            # Step 2: Attempt to delete the manifest
            self.subscriptions.delete()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_negative_delete(self):
        """Upload a manifest with minimal input parameters and attempt to
        delete it but hit 'Cancel' button on confirmation screen

        :id: dbb68a99-2935-4124-8927-e6385e7eecd6

        :BZ: 1266827

        :expectedresults: Manifest was not deleted

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        self.upload_manifest(org.id, manifests.clone())
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.subscriptions.navigate_to_entity()
            self.subscriptions.click(locators['subs.manage_manifest'])
            self.assertTrue(self.subscriptions.wait_until_element_exists(
                 locators['subs.import_history.imported']))
            self.subscriptions.delete(really=False)
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))

    @tier1
    def test_positive_delete_confirmation(self):
        """Upload a manifest with minimal input parameters, press 'Delete'
        button and check warning message on confirmation screen

        :id: 16160ee9-f818-447d-b7ab-d04d396d50c5

        :BZ: 1266827

        :expectedresults: confirmation dialog contains informative message
            which warns user about downsides and consequences of manifest
            deletion

        :CaseImportance: Critical
        """
        expected_message = [
            'Are you sure you want to delete the manifest?',
            'Note: Deleting a subscription manifest is STRONGLY discouraged. '
            'Deleting a manifest will:',
            'Delete all subscriptions that are attached to running hosts.',
            'Delete all subscriptions attached to activation keys.',
            'Disable Red Hat Insights',
            'Require you to upload the subscription-manifest and re-attach '
            'subscriptions to hosts and activation keys.',
            'This action should only be taken in extreme circumstances or for '
            'debugging purposes.',
        ]
        org = entities.Organization().create()
        self.upload_manifest(org.id, manifests.clone())
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.subscriptions.navigate_to_entity()
            self.subscriptions.click(locators['subs.manage_manifest'])
            self.assertTrue(self.subscriptions.wait_until_element_exists(
                locators['subs.import_history.imported']))
            self.subscriptions.click(locators['subs.delete_manifest'])
            actual_message = self.subscriptions.find_element(
                locators['subs.delete_confirmation_message']).text
            try:
                for line in expected_message:
                    self.assertIn(line, actual_message)
            finally:
                self.subscriptions.click(common_locators['close'])

    @stubbed()
    @tier1
    def test_positive_view_future_dated(self):
        """Upload manifest with future-dated subscription and verify that it is
        visible, noted to be future, and the start date is in the future.

        :id: 2a35175f-a4d3-48da-96f1-da78d94b206d

        :steps:

            1. Import a manifest with a future-dated subscription
            2. Navigate to the subscriptions page

        :expectedresults: Future-dated subscription is shown, there is an
            indication it is future, and the start time is in the future.

        :CaseImportance: Critical
        """
        pass

    @tier2
    def test_positive_access_with_non_admin_user_without_manifest(self):
        """Access subscription page with user that has only view_subscriptions
        permission and organization that has no manifest uploaded.

        :id: dab9dc15-39a8-4105-b7ff-ecef909dc6e6

        :expectedresults: Subscription page is rendered properly without errors

        :BZ: 1417082

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        role = entities.Role().create()
        create_role_permissions(
            role,
            {'Katello::Subscription': ['view_subscriptions']}
        )
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            role=[role],
            password=password,
            organization=[org],
            default_organization=org,
        ).create()
        with Session(self, user.login, password):
            self.subscriptions.navigate_to_entity()
            self.assertIsNotNone(self.subscriptions.wait_until_element(
                locators['subs.page_title']))
            self.assertFalse(self.browser.current_url.endswith('katello/403'))

    @tier2
    @upgrade
    def test_positive_access_with_non_admin_user_with_manifest(self):
        """Access subscription page with user that has only view_subscriptions
        permission and organization that has a manifest uploaded.

        :id: 9184fcf6-36be-42c8-984c-3c5d7834b3b4

        :expectedresults: Subscription page is rendered properly without errors
            and the default subscription is visible

        :BZ: 1417082

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        self.upload_manifest(org.id, manifests.clone())
        role = entities.Role().create()
        create_role_permissions(
            role,
            {'Katello::Subscription': ['view_subscriptions']}
        )
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            role=[role],
            password=password,
            organization=[org],
            default_organization=org,
        ).create()
        with Session(self, user.login, password):
            self.subscriptions.navigate_to_entity()
            self.assertFalse(self.browser.current_url.endswith('katello/403'))
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))

    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_view_VDC_subscription_products(self):
        """Ensure that Virtual Datacenters subscription provided products is
        not empty and that a consumed product exist in content products.

        :id: cc4593f0-66ab-4bf6-87d1-d4bd9c89eba5

        :customerscenario: true

        :steps:
            1. Upload a manifest with Virtual Datacenters subscription
            2. Enable a products provided by Virtual Datacenters subscription,
               and synchronize the auto created repository
            3. Create content view with the product repository, and publish it
            4. Create a lifecycle environment and promote the content view to
               it.
            5. Create an activation key with the content view and lifecycle
               environment
            6. Subscribe a host to the activation key
            7. Goto Hosts -> Content hosts and select the created content host
            8. Attach VDC subscription to content host
            9. Goto Content -> Red Hat Subscription
            10. Select Virtual Datacenters subscription

        :expectedresults:
            1. assert that the provided products is not empty
            2. assert that the enabled product is in subscription Product
                Content

        :BZ: 1366327

        :CaseLevel: System
        """
        org = entities.Organization().create()
        subscription = entities.Subscription(organization=org)
        self.upload_manifest(org.id, manifests.clone())
        vds_product_name = PRDS['rhdt']
        vdc_repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=vds_product_name,
            repo=REPOS['rhdt7']['name'],
            reposet=REPOSET['rhdt7'],
            releasever=None,
        )
        vdc_repo = entities.Repository(id=vdc_repo_id)
        vdc_repo.sync()
        content_view = entities.ContentView(
            organization=org, repository=[vdc_repo]).create()
        content_view.publish()
        content_view = content_view.read()
        lce = entities.LifecycleEnvironment(organization=org).create()
        promote(content_view.version[0], lce.id)
        activation_key = entities.ActivationKey(
            organization=org,
            environment=lce,
            content_view=content_view
        ).create()
        # add the default RH subscription
        for sub in subscription.search():
            if sub.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        with VirtualMachine() as vm:
            vm.install_katello_ca()
            vm.register_contenthost(
                org.label, activation_key=activation_key.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                set_context(session, org=org.name)
                self.contenthost.update(
                    vm.hostname,
                    add_subscriptions=[VDC_SUBSCRIPTION_NAME],
                )
                self.assertIsNotNone(self.contenthost.wait_until_element(
                    common_locators['alert.success_sub_form']))
                # ensure that subscription provided products list is not empty
                provided_products = self.subscriptions.get_provided_products(
                    VDC_SUBSCRIPTION_NAME)
                self.assertGreater(len(provided_products), 0)
                # ensure that the product is in provided products
                self.assertIn(vds_product_name, provided_products)
                # ensure that product is in content products
                content_products = self.subscriptions.get_content_products(
                    VDC_SUBSCRIPTION_NAME)
                self.assertEqual(len(content_products), 1)
                self.assertIn(vds_product_name, content_products)

    @skip_if_bug_open('bugzilla', 1487317)
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_view_VDC_guest_subscription_products(self):
        """Ensure that Virtual Data Centers guest subscription Provided
        Products and Content Products are not empty.

        :id: 4a6f6933-8e26-4c47-b544-a300e11a8454

        :customerscenario: true

        :steps:
            1. Upload a manifest with Virtual Datacenters subscription
            2. Config a virtual machine virt-who service for a hypervisor
            3. Ensure virt-who hypervisor host exist
            4. Attach Virtual Datacenters subscription to the virt-who
               hypervisor
            5. Go to Content -> Red Hat Subscription
            6. Select Virtual Datacenters subscription with type Guests of
               virt-who hypervisor

        :expectedresults:
            1. The Virtual Data Centers guests subscription Provided Products
               is not empty and one of the provided products exist
            2. The Virtual Data Centers guests subscription Product Content is
               not empty and one of the consumed products exist

        :BZ: 1395788, 1506636, 1487317

        :CaseLevel: System
        """
        # create a new organization and lifecycle environment
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        provisioning_server = settings.compute_resources.libvirt_hostname
        # Create a new virt-who config
        virt_who_config = make_virt_who_config({
            'organization-id': org.id,
            'hypervisor-type': VIRT_WHO_HYPERVISOR_TYPES['libvirt'],
            'hypervisor-server': 'qemu+ssh://{0}/system'.format(
                provisioning_server),
            'hypervisor-username': 'root',
        })
        # create a virtual machine to host virt-who service
        with VirtualMachine() as virt_who_vm:
            # configure virtual machine and setup virt-who service
            virt_who_data = virt_who_hypervisor_config(
                virt_who_config['general-information']['id'],
                virt_who_vm,
                org_id=org.id,
                lce_id=lce.id,
                hypervisor_hostname=provisioning_server,
                configure_ssh=True,
                subscription_name=VDC_SUBSCRIPTION_NAME,
            )
            virt_who_hypervisor_host = virt_who_data[
                'virt_who_hypervisor_host']
            # RHEL is a content product in this organization (as per virt-who
            # config setup) and also provided by Virtual datacenters
            # subscription then it must exist in provided and content products
            rhel_product_name = PRDS['rhel']
            with Session(self) as session:
                set_context(session, org=org.name)
                # ensure that VDS subscription is assigned to virt-who
                # hypervisor
                self.contenthost.search_and_click(
                    virt_who_hypervisor_host['name'])
                self.contenthost.click(
                    tab_locators['contenthost.tab_subscriptions'])
                self.contenthost.click(
                    tab_locators['contenthost.tab_subscriptions_subscriptions']
                )
                self.assertIsNotNone(
                    self.contenthost.wait_until_element(
                        locators['contenthost.subscription_select']
                        % VDC_SUBSCRIPTION_NAME)
                )
                # ensure that hypervisor guests subscription provided products
                # is not empty
                provided_prd = self.subscriptions.get_guests_provided_products(
                    VDC_SUBSCRIPTION_NAME, virt_who_hypervisor_host['name'])
                self.assertGreater(len(provided_prd), 0)
                self.assertIn(rhel_product_name, provided_prd)
                # ensure that hypervisor guests subscription content products
                # is not empty
                content_prd = self.subscriptions.get_guests_content_products(
                    VDC_SUBSCRIPTION_NAME, virt_who_hypervisor_host['name'])
                self.assertGreater(len(content_prd), 0)
                self.assertIn(rhel_product_name, content_prd)
