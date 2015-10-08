"""Tests for Red Hat Access Insights Client rpm"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.test import TestCase
from robottelo.vm import VirtualMachine


class RHAITestCase(TestCase):

    @classmethod
    def setUpClass(cls):  # noqa
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

        super(RHAITestCase, cls).setUpClass()

    def test_connection_option(self):
        """@Test: Verify that '--test-connection' option for
        redhat-access-insights client rpm tests the connection with the
        satellite server

        @Feature: 'redhat-access-insights --test-connection' will check for the
        connection with satellite server

        @Assert: 'redhat-access-insights --test-connection' should return
        zero on a successfully registered machine to RHAI service
        """
        with VirtualMachine(distro='rhel67') as vm:
            vm.configure_rhai_client(self.ak_name, self.org_label, 'rhel67')
            test_connection = vm.run(
                'redhat-access-insights --test-connection')
            self.logger.info('Return code for --test-connection {0}'.format(
                test_connection.return_code))
            self.assertEqual(test_connection.return_code, 1)
