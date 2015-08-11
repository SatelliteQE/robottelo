"""Tests for Red Hat Access Insights"""


from nailgun import entities
from fauxfactory import gen_string
from robottelo.common.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.common import manifests
from robottelo.test import UITestCase
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator
from robottelo.ui.session import Session


class RHAITestCase(UITestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        # Create a new organization with prefix 'insights'
        org = entities.Organization(
            name='insights_{0}'.format(gen_string('alpha', 6))
        ).create()

        # Upload manifest
        sub = entities.Subscription(organization=org)
        with open(manifests.clone(), 'rb') as manifest:
            sub.upload({'organization_id': org.id}, manifest)

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
        for subs in sub.search():
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

        super(RHAITestCase, cls).setUpClass()

    def test_client_registration_to_rhai(self):
        """@Test: Check for client registration to redhat-access-insights
        service.

        @Feature: RHEL client registration to rhai

        @Assert: Registered client should appear in the Systems sub-menu of Red
        Hat Access Insights

        """
        # Register a VM to Access Insights Service
        self.rhai.register_client_to_rhai(
            self.ak_name,
            self.org_label,
        )

        with Session(self.browser) as session:
            # view clients registered to Red Hat Access Insights
            session.nav.go_to_select_org(self.org_name)
            Navigator(self.browser).go_to_insights_systems()
            result = self.rhai.view_registered_systems()
            self.assertIn("1", result, 'Registered clients are not listed')

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
