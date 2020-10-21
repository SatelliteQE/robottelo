"""Tests for Red Hat Access Insights Client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL6
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.test import TestCase
from robottelo.vm import VirtualMachine


@run_in_one_thread
class RHAIClientTestCase(TestCase):
    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):  # noqa
        super().setUpClass()
        # Create a new organization with prefix 'insights'
        org = entities.Organization(name='insights_{}'.format(gen_string('alpha', 6))).create()

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
            if subs.name == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subs.id})
                break
        cls.org_label = org.label
        cls.ak_name = activation_key.name
        cls.org_name = org.name

    def test_positive_connection_option(self):
        """Verify that '--test-connection' option for redhat-access-insights
        client rpm tests the connection with the satellite server connection
        with satellite server

        :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

        :expectedresults: 'redhat-access-insights --test-connection' should
            return zero on a successfully registered machine to RHAI service
        """
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            vm.configure_rhai_client(self.ak_name, self.org_label, DISTRO_RHEL6)
            test_connection = vm.run('redhat-access-insights --test-connection')
            self.logger.info(f'Return code for --test-connection {test_connection.return_code}')
            self.assertEqual(
                test_connection.return_code, 0, '--test-connection check was not successful'
            )
