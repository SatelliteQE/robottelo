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
from robottelo.api.utils import create_role_permissions
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME

from robottelo.decorators import (
    run_in_one_thread,
    skip_if_not_set,
    tier1,
    tier2,
)

from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@run_in_one_thread
class SubscriptionTestCase(UITestCase):
    """Implements subscriptions/manifests tests in UI"""

    @classmethod
    def set_session_org(cls):
        cls.session_org = entities.Organization().create()

    @skip_if_not_set('fake_manifest')
    @tier1
    def test_positive_upload_and_delete(self):
        """Upload a manifest with minimal input parameters and delete it

        :id: 58e549b0-1ba3-421d-8075-dcf65d07510b

        :expectedresults: Manifest is uploaded and deleted successfully

        :CaseImportance: Critical
        """
        with Session(self.browser):
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
        with Session(self.browser) as session:
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
        with Session(self.browser) as session:
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
                self.subscriptions.click(common_locators['cancel'])

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
        with Session(self.browser, user.login, password):
            self.subscriptions.navigate_to_entity()
            self.assertIsNotNone(self.subscriptions.wait_until_element(
                locators['subs.no_manifests_title']))
            self.assertFalse(self.browser.current_url.endswith('katello/403'))

    @tier2
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
        with Session(self.browser, user.login, password):
            self.subscriptions.navigate_to_entity()
            self.assertFalse(self.browser.current_url.endswith('katello/403'))
            self.assertIsNotNone(
                self.subscriptions.search(DEFAULT_SUBSCRIPTION_NAME))
