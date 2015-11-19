"""Tests for Red Hat Access Insights"""

import time

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.test import UITestCase
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class RHAITestCase(UITestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        super(RHAITestCase, cls).setUpClass()
        # Create a new organization with prefix 'insights'
        org = entities.Organization(
            name='insights_{0}'.format(gen_string('alpha', 6))
        ).create()

        # Upload manifest
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)

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

    def test_client_registration_to_rhai(self):
        """@Test: Check for client registration to redhat-access-insights
        service.

        @Feature: RHEL client registration to rhai

        @Assert: Registered client should appear in the Systems sub-menu of Red
        Hat Access Insights

        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro='rhel67') as vm:
            vm.configure_rhai_client(self.ak_name, self.org_label, 'rhel67')

            with Session(self.browser) as session:
                # view clients registered to Red Hat Access Insights
                session.nav.go_to_select_org(self.org_name)
                Navigator(self.browser).go_to_insights_systems()
                result = self.rhai.view_registered_systems()
                self.assertIn("1", result, 'Registered clients are not listed')
            vm.get('/var/log/redhat-access-insights/redhat-access'
                   '-insights.log', './insights_client_registration.log')

    def test_org_selection_for_rhai(self):
        """@Test: Verify that user attempting to access RHAI is directed to
        select an Organization if there is no organization selected

        @Feature: In order to use Access Insights, user must select an
        organization

        @Assert: 'Organization Selection Required' message must be displayed if
        the user tries to view Access Insights overview without selecting an
        org

        """
        with Session(self.browser) as session:
            # Given that the user does not specify any Organization
            session.nav.go_to_select_org("Any Organization")
            session.nav.go_to_insights_overview()

            # 'Organization Selection Required' message must be present
            result = session.nav.wait_until_element(
                locators['insights.org_selection_msg']).text
            self.assertIn("Organization Selection Required", result)

    def test_unregister_system_from_rhai(self):
        """@Test: Verify that 'Unregister' a system from RHAI works correctly

        @Feature: If a machine if unregistered from the RHAI web interface,
        then the client should be able to use the service.

        @Assert: Once the machine is unregistered from the RHAI web interface
        then the unregistered client machine should return a 1 on running the
        service 'redhat-access-insights'

        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro='rhel71') as vm:
            vm.configure_rhai_client(self.ak_name, self.org_label, 'rhel71')

            with Session(self.browser) as session:
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
                time.sleep(30)

            result = vm.run('redhat-access-insights')
            self.assertEqual(result.return_code, 1,
                             "System has not been unregistered")
            vm.get('/var/log/redhat-access-insights/'
                   'redhat-access-insights.log', './insights_unregister.log')
