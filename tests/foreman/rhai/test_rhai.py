"""Tests for Red Hat Access Insights"""


from nailgun import entities
from fauxfactory import gen_string
from robottelo.common import conf
from robottelo.common.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.common import manifests
from robottelo.ui.navigator import Navigator
from robottelo.ui.session import Session
from robottelo.test import UITestCase
from robottelo.vm import VirtualMachine


class RHAITestCase(UITestCase):
    def test_rhai_client_setup(self):
        """@Test: Check for client registration to redhat-access-insights
        service.

        @Feature: RHEL client registration to rhai

        @Assert: Registered client should appear in the Systems sub-menu of Red
        Hat Access Insights
        """
        # Create a new organization with prefix 'insights'
        org = entities.Organization(
            name='insights_{0}'.format(gen_string('alpha', 6))
        ).create()

        # Upload manifest
        org.upload_manifest(path=manifests.clone())

        # Create activation key using default CV and library environment
        activation_key = entities.ActivationKey(
            auto_attach=True,
            content_view=org.default_content_view.id,
            environment=org.library.id,
            name=gen_string('alpha'),
            organization=org,
        ).create()

        # step 7.1: Walk through the list of subscriptions.
        # Find the "Red Hat Employee Subscription" and attach it to the
        # recently-created activation key.
        for subscription in org.subscriptions():
            if subscription['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions({
                    'quantity': 1,
                    'subscription_id': subscription['id'],
                })
                break

        # Create VM
        with VirtualMachine(distro='rhel66') as vm:
            # Download and Install ketello-ca rpm
            vm.install_katello_cert()
            vm.register_contenthost(activation_key.name, org.label)

            # Red Hat Access Insights requires RHEL 6/7 repo and it not
            # possible to sync the repo during the tests,
            # adding a file in /etc/yum.repos.d/rhel6/7.repo

            rhel6_repo = conf.properties.get('insights.rhel6_repo')

            repo_file = (
                '[rhel6-rpms]\n'
                'name=RHEL6\n'
                'baseurl={0}\n'
                'enabled=1\n'
                .format(rhel6_repo)
            )

            vm.run(
                'echo "{0}" >> /etc/yum.repos.d/rhel6.repo'
                .format(repo_file)
            )

            # Install redhat-access-insights package
            package_name = 'redhat-access-insights'
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)

            # Verify if package is installed by query it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)

            # Register client with Red Hat Access Insights
            result = vm.run('redhat-access-insights --register')
            self.assertEqual(result.return_code, 0)

        with Session(self.browser) as session:
            # view clients registered to Red Hat Access Insights
            session.nav.go_to_select_org(org.name)
            Navigator(self.browser).go_to_insights_systems()
            result = self.rhai.view_registered_systems()
            self.assertIn("1", result, 'Registered clients are not listed')
