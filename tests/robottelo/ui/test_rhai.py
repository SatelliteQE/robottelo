"""Tests for Red Hat Access Insights

:Requirement: Rhai

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string  # noqa
from nailgun import entities  # noqa
from robottelo import manifests  # noqa
from robottelo.api.utils import upload_manifest  # noqa
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME  # noqa
from robottelo.constants import DISTRO_RHEL6, DISTRO_RHEL7  # noqa
from robottelo.decorators import run_in_one_thread, skip_if_not_set  # noqa
from robottelo.test import UITestCase  # noqa
from robottelo.ui.factory import set_context  # noqa
from robottelo.ui.locators import common_locators, menu_locators
from robottelo.ui.session import Session  # noqa
from robottelo.vm import VirtualMachine  # noqa


# pylint: enable=import-error,wrong-import-position
# error

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

    def test_rhai_navigation(self):
        """Test navigation across RHAI tab

        :expectedresults: All pages should be opened correctly without 500
            error
        """
        pages = [
            'rhai_overview',
            'rhai_inventory',
            'rhai_manage'
        ]
        with Session(self) as session:
            set_context(session, org=self.org_name, force_context=True)
            for page in pages:
                getattr(session, page).navigate_to_entity()
                self.assertIsNotNone(session.nav.wait_until_element(
                    menu_locators['menu.current_text']))
                self.assertIsNone(session.nav.wait_until_element(
                    common_locators['alert.error'], timeout=1))
                self.assertIsNone(session.nav.wait_until_element(
                    common_locators['notif.error'], timeout=1))

    def test_rhai_manage_service(self):
        with Session(self) as session:
            set_context(session, org=self.org_name, force_context=True)
            session.rhai_manage.disable_service()
            assert not session.rhai_manage.is_service_enabled
            session.rhai_manage.enable_service()
            assert session.rhai_manage.is_service_enabled

    def test_rhai_manage_insights_connection(self):
        with Session(self) as session:
            set_context(session, org=self.org_name, force_context=True)
            session.rhai_manage.check_connection()
            assert session.rhai_manage.is_insights_engine_connected

