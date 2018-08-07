"""Tests for Red Hat Access Insights Client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import (DEFAULT_SUBSCRIPTION_NAME, DISTRO_RHEL6,
                                 DISTRO_RHEL7)
from robottelo.decorators import run_in_one_thread, skip_if_not_set
from robottelo.test import TestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class RHAIClientTestCase(TestCase):

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):  # noqa
        super(RHAIClientTestCase, cls).setUpClass()
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

    def test_positive_connection_option(self):
        """Verify that '--test-connection' option for insights-client rpm tests
        the connection with the satellite server connection with satellite
        server

        :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

        :expectedresults: 'insights-client --test-connection' should
            return zero on a successfully registered machine to RHAI service
        """
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            vm.configure_rhai_client(self.ak_name, self.org_label,
                                     DISTRO_RHEL6)
            test_connection = vm.run(
                'insights-client --test-connection')
            self.logger.info('Return code for --test-connection {0}'.format(
                test_connection.return_code))
            self.assertEqual(test_connection.return_code, 0,
                             '--test-connection check was not successful')

    def test_provision(self):
        """A new host appears in Red Hat Access Insights inventory

        :id: 0bf2bccf-0973-49fa-923f-7409fba86f85

        :expectedresults: provisioned host is in the inventory
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.configure_rhai_client(
                activation_key=self.ak_name,
                org=self.org_label,
                rhel_distro=DISTRO_RHEL7)
            self.assertIn(
                'Client: 3.',
                vm.run('insights-client --version').stdout[0],
            )
            with Session(self) as session:
                set_context(session, org=self.org_label)
                vm_info = session.hosts.get_host_properties(
                    vm.hostname,
                    ['Status', 'Operating system', 'Subscription'])
                self.assertEqual(vm_info['Status'], 'OK')
                self.assertEqual(vm_info['Subscription'], 'Fully entitled')
                self.assertTrue(
                    session.rhai_inventory.search(vm.hostname).is_displayed())

    def test_numeric_group(self):
        """Check the rule appears when provoked and disappears on Satellite
        once applied

        :id: 4562e0f9-fff1-4cc7-b7e7-e4779662b3e1

        :expectedresults: rule no more appears on Rules page on portal
        """
        message = 'group names are numeric'
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.configure_rhai_client(
                activation_key=self.ak_name,
                org=self.org_label,
                rhel_distro=DISTRO_RHEL7)

            with Session(self) as session:
                set_context(session, org=self.org_label)

                session.rhai_inventory.search_and_click(vm.hostname)
                self.assertIsNotNone(
                    session.nav.wait_until_element(
                        locators['insights.rules.modal_window']))
                self.assertIsNotNone(
                    session.nav.wait_until_element(
                        locators['insights.rules.rule_summary']))
                rules = session.browser.find_elements_by_class_name(
                    'rule-summary')

                self.assertFalse(
                    any([message in rule.text for rule in rules]))

                vm.run('groupadd 123456')
                vm.run('insights-client')

                session.rhai_inventory.click(
                    locators["insights.rules.close_modal"])
                session.rhai_inventory.search_and_click(vm.hostname)
                self.assertIsNotNone(session.nav.wait_until_element(
                    locators['insights.rules.rule_summary']))
                rules = session.browser.find_elements_by_class_name(
                    'rule-summary')

                # New rule appeared
                self.assertTrue(
                    any([message in rule.text for rule in rules]))

                vm.run('groupdel 123456')
                vm.run('insights-client')

                session.rhai_inventory.click(
                    locators["insights.rules.close_modal"])
                session.rhai_inventory.search_and_click(vm.hostname)
                self.assertIsNotNone(session.nav.wait_until_element(
                    locators['insights.rules.rule_summary']))
                rules = session.browser.find_elements_by_class_name(
                    'rule-summary')
                # Rule doesn't show up since it's been applied
                self.assertFalse(
                    any([message in rule.text for rule in rules]))
