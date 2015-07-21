"""Tests for Red Hat Access Insights"""


from nailgun import entities
from fauxfactory import gen_string
from robottelo.common import conf
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

        # Create new lifecycle environment
        lifecycle_env = entities.LifecycleEnvironment(
            name='rhai_env_{0}'.format(gen_string('alpha', 6)),
            organization=org,
        ).create()

        # Upload manifest
        org.upload_manifest(path=manifests.clone())

        # Create a custom product for RHAI
        custom_product = entities.Product(
            name='rhai_product_{0}'.format(gen_string('alpha', 6)),
            organization=org,
        ).create()

        # Add insights repo to the custom product
        custom_repo = entities.Repository(
            content_type=u'yum',
            name=u'insights_repo_{0}'.format(gen_string('alpha', 6)),
            product=custom_product,
            url=u'http://access.redhat.com/insights/repo/6/',
        ).create()

        # Sync custom repository
        custom_repo.sync()

        # Create content view
        content_view = entities.ContentView(
            name='rhai_cv_{0}'.format(gen_string('alpha', 6)),
            organization=org,
        ).create()

        # Associate custom repository to new content view
        content_view.set_repository_ids([custom_repo.id])

        # Publish content view
        content_view.publish()

        # Promote content view to lifecycle_env
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view.version[0].promote(lifecycle_env.id)

        # Create activation key
        activation_key = entities.ActivationKey(
            auto_attach=True,
            content_view=content_view,
            environment=lifecycle_env,
            name=gen_string('alpha'),
            organization=org,
        ).create()

        for subscription in org.subscriptions():
            # Attach custom product subscription to the activation key
            if subscription['product_name'] == custom_product.name:
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
