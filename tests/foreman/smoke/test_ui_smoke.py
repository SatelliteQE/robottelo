"""Smoke tests for the ``UI`` end-to-end scenario."""

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
    GOOGLE_CHROME_REPO,
    LIBVIRT_RESOURCE_URL,
    PRDS,
    REPOS,
    REPOSET,
    REPO_TYPE,
    RHVA_REPO_TREE,
    SAT6_TOOLS_TREE,
    FAKE_6_PUPPET_REPO,
)
from robottelo.decorators import bz_bug_is_open, skip_if_not_set
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


class SmokeTestCase(UITestCase):
    """End-to-end tests using the ``WebUI``."""

    def test_positive_find_default_org(self):
        """@Test: Check if :data:`robottelo.constants.DEFAULT_ORG` is present

        @Feature: Smoke Test

        @Assert: 'Default Organization' is found

        """
        with Session(self.browser) as session:
            self.assertEqual(
                session.nav.go_to_select_org(DEFAULT_ORG),
                DEFAULT_ORG
            )

    def test_positive_find_default_loc(self):
        """@Test: Check if :data:`robottelo.constants.DEFAULT_LOC` is present

        @Feature: Smoke Test

        @Assert: 'Default Location' is found

        """
        with Session(self.browser) as session:
            self.assertEqual(
                session.nav.go_to_select_loc(DEFAULT_LOC),
                DEFAULT_LOC
            )

    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        @Feature: Smoke Test

        @Assert: Admin User is found and has Admin role

        """
        with Session(self.browser):
            self.assertTrue(self.user.user_admin_role_toggle('admin'))

    def test_positive_smoke(self):
        """Check that basic content can be created

        * Create a new user with admin permissions
        * Using the new user from above:

            * Create a new organization
            * Create two new lifecycle environments
            * Create a custom product
            * Create a custom YUM repository
            * Create a custom PUPPET repository
            * Synchronize both custom repositories
            * Create a new content view
            * Associate both repositories to new content view
            * Publish content view
            * Promote content view to both lifecycles
            * Create a new libvirt compute resource
            * Create a new subnet
            * Create a new domain
            * Create a new hostgroup and associate previous entities to it

        @Feature: Smoke Test

        @Assert: All entities are created and associated.

        """
        user_name = gen_string('alpha')
        password = gen_string('alpha')
        org_name = gen_string('alpha')
        env_1_name = gen_string('alpha')
        env_2_name = gen_string('alpha')
        product_name = gen_string('alpha')
        yum_repository_name = gen_string('alpha')
        puppet_repository_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        compute_resource_name = gen_string('alpha')
        subnet_name = gen_string('alpha')
        domain_name = gen_string('alpha')
        domain = DOMAIN % domain_name
        hostgroup_name = gen_string('alpha')

        # Create new user with admin permissions
        with Session(self.browser) as session:
            make_user(
                session,
                username=user_name,
                password1=password,
                password2=password
            )
            self.assertIsNotNone(self.user.search(user_name))
            self.assertTrue(self.user.user_admin_role_toggle(user_name))

        # FIX ME: UI doesn't authenticate user created via UI auto: Issue #1152
        # Once #1152 is fixed; need to pass user_name and password to Session
        with Session(self.browser) as session:
            # Create New organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

            # Create New Lifecycle environment1
            make_lifecycle_environment(session, org=org_name, name=env_1_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(env_1_name))
            # Create New  Lifecycle environment2
            make_lifecycle_environment(
                session,
                org=org_name,
                name=env_2_name,
                prior=env_1_name
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(env_2_name))

            # Create custom product
            make_product(session, org=org_name, name=product_name)
            product = self.products.search(product_name)
            self.assertIsNotNone(product)

            # Create a YUM repository
            product.click()
            make_repository(
                session,
                name=yum_repository_name,
                url=GOOGLE_CHROME_REPO
            )
            self.assertIsNotNone(self.repository.search(yum_repository_name))

            # Create a puppet Repository
            self.products.search(product_name).click()
            make_repository(
                session,
                name=puppet_repository_name,
                url=FAKE_0_PUPPET_REPO,
                repo_type=REPO_TYPE['puppet']
            )
            self.assertIsNotNone(self.repository.search(
                puppet_repository_name
            ))

            # Sync YUM and puppet repository
            self.navigator.go_to_sync_status()
            self.assertIsNotNone(self.sync.sync_custom_repos(
                product_name,
                [yum_repository_name, puppet_repository_name]
            ))

            # Create new content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))

            # Add YUM repository to content-view
            self.content_views.add_remove_repos(cv_name, [yum_repository_name])
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Add puppet-module to content-view
            if not bz_bug_is_open(1297308):
                self.content_views.add_puppet_module(
                    cv_name, 'httpd', filter_term='Latest'
                )

            # Publish content-view
            self.content_views.publish(cv_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Promote content-view to life-cycle environment 1
            self.content_views.promote(
                cv_name, version='Version 1', env=env_1_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Promote content-view to life-cycle environment 2
            self.content_views.promote(
                cv_name, version='Version 1', env=env_2_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Create a new libvirt compute resource
            url = (
                LIBVIRT_RESOURCE_URL % settings.server.hostname
            )
            make_resource(
                session,
                org=org_name,
                name=compute_resource_name,
                provider_type=FOREMAN_PROVIDERS['libvirt'],
                parameter_list=[['URL', url, 'field']],
            )
            self.assertIsNotNone(
                self.compute_resource.search(compute_resource_name))

            # Create a subnet
            make_subnet(
                session,
                org=org_name,
                subnet_name=subnet_name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask='255.255.255.0'
            )
            self.assertIsNotNone(self.subnet.search(subnet_name))

            # Create a Domain
            make_domain(
                session,
                org=org_name,
                name=domain,
                description=domain
            )
            self.assertIsNotNone(self.domain.search(domain))

            # Create a HostGroup
            make_hostgroup(session, name=hostgroup_name)
            self.assertIsNotNone(self.hostgroup.search(hostgroup_name))

    @skip_if_not_set('clients')
    def test_positive_end_to_end(self):
        """Perform end to end smoke tests using RH repos.

        @Feature: Smoke test

        @Assert: All tests should succeed and Content should be successfully
        fetched by client

        """
        org_name = gen_string('alpha', 6)
        cv_name = gen_string('alpha', 6)
        activation_key_name = gen_string('alpha', 6)
        env_name = gen_string('alpha', 6)
        repos = self.sync.create_repos_tree(RHVA_REPO_TREE)
        with Session(self.browser) as session:
            # Create New organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            # Create New Lifecycle environment
            make_lifecycle_environment(session, org=org_name, name=env_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(env_name))
            # Navigate UI to select org and redhat subscription page
            session.nav.go_to_select_org(org_name)
            session.nav.go_to_red_hat_subscriptions()
            # Upload manifest from webui
            with manifests.clone() as manifest:
                self.subscriptions.upload(manifest)
            self.assertTrue(session.nav.wait_until_element(
                common_locators['alert.success']
            ))
            session.nav.go_to_red_hat_repositories()
            # List of dictionary passed to enable the redhat repos
            # It selects Product->Reposet-> Repo
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            # Sync the repos
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(self.sync.sync_rh_repos(repos))
            # Create new content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add YUM repository to content-view
            self.content_views.add_remove_repos(
                cv_name,
                [REPOS['rhva65']['name'], REPOS['rhva6']['name']]
            )
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))
            # Publish content-view
            self.content_views.publish(cv_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
                ))

            # Promote content-view to life-cycle environment 1
            self.content_views.promote(
                cv_name, version='Version 1', env=env_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
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
                activation_key_name, [DEFAULT_SUBSCRIPTION_NAME])
            self.activationkey.enable_repos(
                activation_key_name, [REPOSET['rhva6']])
            if not bz_bug_is_open(1191541):
                self.assertIsNotNone(self.activationkey.wait_until_element(
                    common_locators['alert.success']
                ))
            # Create VM
            with VirtualMachine(distro='rhel66') as vm:
                vm.install_katello_ca()
                result = vm.register_contenthost(activation_key_name, org_name)
                self.assertEqual(result.return_code, 0)

                # Install contents from sat6 server
                package_name = 'python-kitchen'
                result = vm.run(u'yum install -y {0}'.format(package_name))
                self.assertEqual(result.return_code, 0)
                # Verify if package is installed by query it
                result = vm.run(u'rpm -q {0}'.format(package_name))
                self.assertEqual(result.return_code, 0)

    @skip_if_not_set('clients')
    def test_positive_puppet_install(self):
        """Perform puppet end to end smoke tests using RH repos.

        @Feature: Smoke test puppet install and configure on client

        @Assert: Client should get configured by puppet-module.

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
            session.nav.go_to_red_hat_repositories()
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
                    common_locators['alert.success']
                ))
            # Promote content-view to life-cycle environment.
            self.content_views.promote(
                cv_name, version='Version 1', env=env_name)
            if not bz_bug_is_open(1191422):
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']
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
                vm.register_contenthost(activation_key_name, org_name)
                vm.configure_puppet(rhel6_repo)
                host = vm.hostname
                set_context(session, org=ANY_CONTEXT['org'])
                session.nav.go_to_hosts()
                self.hosts.update_host_bulkactions(host=host, org=org_name)
                self.hosts.update(
                    name=host,
                    lifecycle_env=env_name,
                    cv=cv_name,
                    reset_puppetenv=True,
                )
                session.nav.go_to_hosts()
                self.hosts.update(
                    name=host,
                    reset_puppetenv=False,
                    puppet_module=puppet_module
                )
                vm.run(u'puppet agent -t')
                result = vm.run(u'cat /etc/motd | grep FQDN')
                self.assertEqual(result.return_code, 0)
