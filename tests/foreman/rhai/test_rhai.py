"""Tests for Red Hat Access Insights

:Requirement: Rhai

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import time
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL6, DISTRO_RHEL7
from robottelo.decorators import run_in_one_thread, skip_if_not_set
from robottelo.test import UITestCase
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class RHAITestCase(UITestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        super(RHAITestCase, cls).setUpClass()
        # Create a new organization with prefix 'insights'
        org = entities.Organization(
            name='insights_{0}'.format(gen_string('alpha', 6))
        ).create()

        # Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

        # Create activation key using default CV and library environment
        activation_key = entities.ActivationKey(
            auto_attach=True,
            content_view=org.default_content_view.id,
            environment=org.library.id,
            name=gen_string('alpha'),
            organization=org,
        ).create()

        # Walk through the list of subscriptions.
        # Find the "Red Hat Employee Subscription" and attach it to the
        # recently-created activation key.
        for subs in entities.Subscription(organization=org).search():
            if subs.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': subs.id,
                })
                break
        cls.org_label = org.label
        cls.ak_name = activation_key.name
        cls.org_name = org.name

    @skip_if_not_set('clients')
    def test_positive_register_client_to_rhai(self):
        """Check client registration to redhat-access-insights service.

        :id: f3aefdb3-ac99-402d-afd9-e53e9ee1e8d7

        :expectedresults: Registered client should appear in the Systems sub-
            menu of Red Hat Access Insights
        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            try:
                vm.configure_rhai_client(self.ak_name, self.org_label,
                                         DISTRO_RHEL6)

                with Session(self) as session:
                    # view clients registered to Red Hat Access Insights
                    session.nav.go_to_select_org(self.org_name)
                    Navigator(self.browser).go_to_insights_systems()
                    result = self.rhai.view_registered_systems()
                    self.assertIn("1", result,
                                  'Registered clients are not listed')
            finally:
                vm.get('/var/log/redhat-access-insights/'
                       'redhat-access-insights.log',
                       './insights_client_registration.log')

    def test_negative_org_not_selected(self):
        """Verify that user attempting to access RHAI is directed to select an
        Organization if there is no organization selected

        :id: 6ddfdb29-eeb5-41a4-8851-ad19130b112c

        :expectedresults: 'Organization Selection Required' message must be
            displayed if the user tries to view Access Insights overview
            without selecting an org
        """
        with Session(self) as session:
            # Given that the user does not specify any Organization
            session.nav.go_to_select_org("Any Organization")
            session.nav.go_to_insights_overview()

            # 'Organization Selection Required' message must be present
            result = session.nav.wait_until_element(
                locators['insights.org_selection_msg']).text
            self.assertIn("Organization Selection Required", result)

    @skip_if_not_set('clients')
    def test_positive_unregister_client_from_rhai(self):
        """Verify that 'Unregister' a system from RHAI works correctly then the
        system should not be able to use the service.

        :id: 580f9704-8c6d-4f63-b027-68a6ac97af77

        :expectedresults: Once the system is unregistered from the RHAI web
            interface then the unregistered system should return `1` on running
            the service 'redhat-access-insights'
        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            try:
                vm.configure_rhai_client(self.ak_name, self.org_label,
                                         DISTRO_RHEL7)

                with Session(self) as session:
                    session.nav.go_to_select_org(self.org_name)
                    Navigator(self.browser).go_to_insights_systems()
                    # Click on the unregister icon 'X' in the table against the
                    # registered system listed.
                    strategy, value = locators['insights.unregister_system']
                    session.nav.click(
                        (strategy, value % vm.hostname),
                        wait_for_ajax=True,
                        ajax_timeout=40,
                    )

                    # Confirm selection for clicking on 'Yes' to unregister the
                    # system
                    session.nav.click(
                        locators['insights.unregister_button']
                    )
                    self.browser.refresh()
                    time.sleep(60)
                    self.browser.refresh()

                result = vm.run('redhat-access-insights')
                self.assertEqual(result.return_code, 1,
                                 "System has not been unregistered")
            finally:
                vm.get('/var/log/redhat-access-insights/'
                       'redhat-access-insights.log',
                       './insights_unregister.log')
