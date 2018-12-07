"""Test class for Subscriptions/Manifests UI

:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo import manifests


from robottelo.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
)

from robottelo.decorators import (
    run_in_one_thread,
    skip_if_not_set,
    stubbed,
    tier1,
    upgrade,
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
