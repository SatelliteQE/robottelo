# coding=utf-8
"""Smoke tests for the ``UI`` end-to-end scenario.

@Requirement: Ui endtoend

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string, gen_ipaddr
from robottelo import manifests
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_SUBSCRIPTION_NAME,
    DISTRO_RHEL6,
    DOMAIN,
    FAKE_0_PUPPET_REPO,
    FOREMAN_PROVIDERS,
    CUSTOM_RPM_REPO,
    LIBVIRT_RESOURCE_URL,
    PRDS,
    REPOS,
    REPOSET,
    REPO_TYPE,
    RHVA_REPO_TREE,
    SAT6_TOOLS_TREE,
    FAKE_6_PUPPET_REPO,
)
from robottelo.decorators import (
    bz_bug_is_open,
    setting_is_set,
    skip_if_not_set,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_activationkey,
    make_contentview,
    make_domain,
    make_hostgroup,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_resource,
    make_subnet,
    make_user,
    set_context,
)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine
from .utils import ClientProvisioningMixin


class EndToEndTestCase(UITestCase, ClientProvisioningMixin):
    """End-to-end tests using the ``WebUI``."""

    @classmethod
    def setUpClass(cls):  # noqa
        super(EndToEndTestCase, cls).setUpClass()
        cls.fake_manifest_is_set = setting_is_set('fake_manifest')

    def test_positive_find_default_org(self):
        """@Test: Check if :data:`robottelo.constants.DEFAULT_ORG` is present

        @id: 90646b0a-ce56-43cf-8cd7-2b4586478acc

        @expectedresults: 'Default Organization' is found
        """
        with Session(self.browser) as session:
            self.assertEqual(
                session.nav.go_to_select_org(DEFAULT_ORG),
                DEFAULT_ORG
            )

    def test_positive_find_default_loc(self):
        """@Test: Check if :data:`robottelo.constants.DEFAULT_LOC` is present

        @id: 4b7cc80b-7368-4ee4-8aaf-c946968e49a4

        @expectedresults: 'Default Location' is found
        """
        with Session(self.browser) as session:
            self.assertEqual(
                session.nav.go_to_select_loc(DEFAULT_LOC),
                DEFAULT_LOC
            )

    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        @id: 9cab1b65-70af-4245-98cb-7da90a98d347

        @expectedresults: Admin User is found and has Admin role
        """
        with Session(self.browser):
            self.assertTrue(self.user.user_admin_role_toggle('admin'))

    @skip_if_not_set('compute_resources')
    def test_positive_end_to_end(self):
        """Perform end to end smoke tests using RH and custom repos.

        1. Create a new user with admin permissions
        2. Using the new user from above
            1. Create a new organization
            2. Clone and upload manifest
            3. Create a new lifecycle environment
            4. Create a custom product
            5. Create a custom YUM repository
            6. Create a custom PUPPET repository
            7. Enable a Red Hat repository
            8. Synchronize the three repositories
            9. Create a new content view
            10. Associate the YUM and Red Hat repositories to new content view
            11. Add a PUPPET module to new content view
            12. Publish content view
            13. Promote content view to the lifecycle environment
            14. Create a new activation key
            15. Add the products to the activation key
            16. Create a new libvirt compute resource
            17. Create a new subnet
            18. Create a new domain
            19. Create a new hostgroup and associate previous entities to it
            20. Provision a client

        @id: 6b7c6187-3cc2-4bd3-89f2-fa7a5f570986

        @expectedresults: All tests should succeed and Content should be
        successfully fetched by client.
        """
        activation_key_name = gen_string('alpha')
        compute_resource_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        domain_name = DOMAIN % gen_string('alpha')
        hostgroup_name = gen_string('alpha')
        lce_name = gen_string('alpha')
        org_name = gen_string('alpha')
        password = gen_string('alpha')
        product_name = gen_string('alpha')
        puppet_repository_name = gen_string('alpha')
        if self.fake_manifest_is_set:
            repos = self.sync.create_repos_tree(RHVA_REPO_TREE)
        subnet_name = gen_string('alpha')
        username = gen_string('alpha')
        yum_repository_name = gen_string('alpha')

        # step 1: Create a new user with admin permissions
        with Session(self.browser) as session:
            make_user(
                session,
                admin=True,
                password1=password,
                password2=password,
                username=username,
            )
            self.assertIsNotNone(self.user.search(username))
            self.assertTrue(self.user.user_admin_role_toggle(username))

        with Session(self.browser, username, password) as session:
            # step 2.1: Create a new organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

            # step 2.2: Clone and upload manifest
            if self.fake_manifest_is_set:
                session.nav.go_to_select_org(org_name)
                session.nav.go_to_red_hat_subscriptions()
                with manifests.clone() as manifest:
                    self.subscriptions.upload(manifest)
                self.assertTrue(session.nav.wait_until_element(
                    common_locators['alert.success']
                ))

            # step 2.3: Create a new lifecycle environment
            make_lifecycle_environment(session, org=org_name, name=lce_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(lce_name))

            # step 2.4: Create a custom product
            make_product(session, org=org_name, name=product_name)
            self.assertIsNotNone(self.products.search(product_name))

            # step 2.5: Create custom YUM repository
            self.products.search(product_name).click()
            make_repository(
                session,
                name=yum_repository_name,
                url=CUSTOM_RPM_REPO
            )
            self.assertIsNotNone(self.repository.search(yum_repository_name))

            # step 2.6: Create custom PUPPET repository
            self.products.search(product_name).click()
            make_repository(
                session,
                name=puppet_repository_name,
                url=FAKE_0_PUPPET_REPO,
                repo_type=REPO_TYPE['puppet']
            )
            self.assertIsNotNone(
                self.repository.search(puppet_repository_name))

            # step 2.7: Enable a Red Hat repository
            if self.fake_manifest_is_set:
                self.sync.enable_rh_repos(repos)

            # step 2.8: Synchronize the three repositories
            self.navigator.go_to_sync_status()
            self.assertIsNotNone(self.sync.sync_custom_repos(
                product_name,
                [yum_repository_name, puppet_repository_name]
            ))
            if self.fake_manifest_is_set:
                self.assertTrue(self.sync.sync_rh_repos(repos))

            # step 2.9: Create content view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))

            self.content_views.add_remove_repos(cv_name, [yum_repository_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']
            ))

            # step 2.10: Associate the YUM and Red Hat repositories to new
            # content view
            repositories = [yum_repository_name]
            if self.fake_manifest_is_set:
                repositories.append(REPOS['rhva65']['name'])
                repositories.append(REPOS['rhva6']['name'])
            self.content_views.add_remove_repos(cv_name, repositories)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']
            ))

            # step 2.11: Add a PUPPET module to new content view
            self.content_views.add_puppet_module(
                cv_name, 'httpd', filter_term='Latest')

            # step 2.12: Publish content view
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']
            ))

            # step 2.13: Promote content view to the lifecycle environment
            self.content_views.promote(
                cv_name, version='Version 1', env=lce_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']
            ))

            # step 2.14: Create a new activation key
            make_activationkey(
                session,
                org=org_name,
                name=activation_key_name,
                env=lce_name,
                content_view=cv_name
            )
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success']
            ))

            # step 2.15: Add the products to the activation key
            self.activationkey.associate_product(
                activation_key_name, [DEFAULT_SUBSCRIPTION_NAME])

            # step 2.15.1: Enable product content
            if self.fake_manifest_is_set:
                self.activationkey.enable_repos(
                    activation_key_name, [REPOSET['rhva6']])

            # step 2.16: Create a new libvirt compute resource
            make_resource(
                session,
                org=org_name,
                name=compute_resource_name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[[
                    'URL',
                    (LIBVIRT_RESOURCE_URL %
                     settings.compute_resources.libvirt_hostname),
                    'field'
                ]],
            )
            self.assertIsNotNone(
                self.compute_resource.search(compute_resource_name))

            # step 2.17: Create a new subnet
            make_subnet(
                session,
                org=org_name,
                subnet_name=subnet_name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask='255.255.255.0'
            )
            self.assertIsNotNone(self.subnet.search(subnet_name))

            # step 2.18: Create a new domain
            make_domain(
                session,
                org=org_name,
                name=domain_name,
                description=domain_name
            )
            self.assertIsNotNone(self.domain.search(domain_name))

            # step 2.19: Create a new hostgroup and associate previous entities
            # to it
            make_hostgroup(session, name=hostgroup_name)
            self.assertIsNotNone(self.hostgroup.search(hostgroup_name))

        # step 2.20: Provision a client
        self.client_provisioning(activation_key_name, org_name)

    @skip_if_not_set('clients')
    def test_positive_puppet_install(self):
        """Perform puppet end to end smoke tests using RH repos.

        @id: 30b0f872-d035-431a-988f-2b3fde620c78

        @expectedresults: Client should get configured by puppet-module.
        """
        activation_key_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        org_name = gen_string('alpha')
        product_name = gen_string('alpha')
        puppet_module = 'motd'
        puppet_repository_name = gen_string('alpha')
        repos = self.sync.create_repos_tree(SAT6_TOOLS_TREE)
        rhel_prd = DEFAULT_SUBSCRIPTION_NAME
        if settings.rhel6_repo is None:
            self.skipTest('Missing configuration for rhel6_repo')
        rhel6_repo = settings.rhel6_repo
        with Session(self.browser) as session:
            # Create New organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            # Create New Lifecycle environment
            make_lifecycle_environment(session, org=org_name, name=env_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(env_name))
            session.nav.go_to_red_hat_subscriptions()
            # Upload manifest from webui
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(session.nav.wait_until_element(
                common_locators['alert.success']
            ))
            # List of dictionary passed to enable the redhat repos
            # It selects Product->Reposet-> Repo
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            # Sync the repos
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(self.sync.sync_noversion_rh_repos(
                PRDS['rhel'], [REPOS['rhst6']['name']]
            ))
            # Create custom product
            make_product(session, org=org_name, name=product_name)
            product = self.products.search(product_name)
            self.assertIsNotNone(product)
            # Create a puppet Repository
            product.click()
            make_repository(
                session,
                name=puppet_repository_name,
                url=FAKE_6_PUPPET_REPO,
                repo_type=REPO_TYPE['puppet']
            )
            self.assertIsNotNone(self.repository.search(
                puppet_repository_name
            ))
            # Sync the repos
            # syn.sync_rh_repos returns boolean values and not objects
            session.nav.go_to_sync_status()
            self.assertIsNotNone(self.sync.sync_custom_repos(
                product_name,
                [puppet_repository_name]
            ))
            # Create new content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add YUM repository to content-view
            self.content_views.add_remove_repos(
                cv_name,
                [REPOS['rhst6']['name']],
            )
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Add puppet-module to content-view
            self.content_views.add_puppet_module(
                cv_name, puppet_module, filter_term='Latest')
            # Publish content-view
            self.content_views.publish(cv_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form']
                ))
            # Promote content-view to life-cycle environment.
            self.content_views.promote(
                cv_name, version='Version 1', env=env_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form']
                ))
            # Create Activation-Key
            make_activationkey(
                session,
                org=org_name,
                name=activation_key_name,
                env=env_name,
                content_view=cv_name
            )
            self.activationkey.associate_product(
                activation_key_name, [product_name, rhel_prd])
            self.activationkey.enable_repos(
                activation_key_name, [REPOSET['rhst6']]
            )
            if not bz_bug_is_open(1191541):
                self.assertIsNotNone(self.activationkey.wait_until_element(
                    common_locators['alert.success']
                ))
            # Create VM
            with VirtualMachine(distro=DISTRO_RHEL6) as vm:
                vm.install_katello_ca()
                vm.register_contenthost(org_name, activation_key_name)
                vm.configure_puppet(rhel6_repo)
                host = vm.hostname
                set_context(session, org=ANY_CONTEXT['org'])
                self.hosts.update_host_bulkactions(
                    [host],
                    action='Assign Organization',
                    parameters_list=[{'organization': org_name}],
                )
                self.hosts.update(
                    name=host.split('.')[0],
                    domain_name=vm.domain,
                    parameters_list=[
                        ['Host', 'Lifecycle Environment', env_name],
                        ['Host', 'Content View', cv_name],
                        ['Host', 'Reset Puppet Environment', True],
                    ],
                    puppet_classes=[puppet_module]
                )
                vm.run(u'puppet agent -t')
                result = vm.run(u'cat /etc/motd | grep FQDN')
                self.assertEqual(result.return_code, 0)
