"""Smoke tests for the ``UI`` end-to-end scenario."""

from ddt import ddt
from fauxfactory import gen_string, gen_ipaddr
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common import manifests
from robottelo.common.constants import (
    FAKE_0_PUPPET_REPO, GOOGLE_CHROME_REPO, REPO_TYPE, FOREMAN_PROVIDERS,
    DOMAIN, DEFAULT_ORG, DEFAULT_LOC, RHVA_REPO_TREE)
from robottelo.common.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_user, make_org,
                                  make_lifecycle_environment, make_product,
                                  make_repository, make_contentview,
                                  make_resource, make_subnet, make_domain,
                                  make_hostgroup, make_activationkey)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@ddt
class TestSmoke(UITestCase):
    """End-to-end tests using the ``WebUI``."""

    @attr('smoke')
    def test_find_default_org(self):
        """@Test: Check if :data:`robottelo.common.constants.DEFAULT_ORG`
        is present

        @Feature: Smoke Test

        @Assert: 'Default Organization' is found

        """

        with Session(self.browser) as session:
            selected_org = session.nav.go_to_select_org(DEFAULT_ORG)
            self.assertEqual(selected_org, DEFAULT_ORG)

    @attr('smoke')
    def test_find_default_location(self):
        """@Test: Check if :data:`robottelo.common.constants.DEFAULT_LOC`
        is present

        @Feature: Smoke Test

        @Assert: 'Default Location' is found

        """

        with Session(self.browser) as session:
            selected_loc = session.nav.go_to_select_loc(DEFAULT_LOC)
            self.assertEqual(selected_loc, DEFAULT_LOC)

    @attr('smoke')
    def test_find_admin_user(self):
        """@Test: Check if Admin User is present

        @Feature: Smoke Test

        @Assert: Admin User is found and has Admin role

        """

        with Session(self.browser) as session:
            session.nav.go_to_users()
            element = self.user.search("admin", search_key="login")
            self.assertIsNotNone(element)
            is_admin_role_selected = self.user.admin_role_to_user("admin")
            self.assertTrue(is_admin_role_selected)

    @attr('smoke')
    def test_smoke(self):
        """@Test: Check that basic content can be created

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

        user_name = gen_string("alpha", 6)
        password = gen_string("alpha", 6)
        org_name = gen_string("alpha", 6)
        env_1_name = gen_string("alpha", 6)
        env_2_name = gen_string("alpha", 6)
        product_name = gen_string("alpha", 6)
        yum_repository_name = gen_string("alpha", 6)
        puppet_repository_name = gen_string("alpha", 6)
        cv_name = gen_string("alpha", 6)
        puppet_module = "httpd"
        module_ver = 'Latest'
        compute_resource_name = gen_string("alpha", 6)
        libvirt_url = "qemu+tcp://%s:16509/system"
        provider_type = FOREMAN_PROVIDERS['libvirt']
        url = (libvirt_url % conf.properties['main.server.hostname'])
        subnet_name = gen_string("alpha", 6)
        domain_name = gen_string("alpha", 6)
        domain = description = DOMAIN % domain_name
        hostgroup_name = gen_string("alpha", 6)

        # Create new user with admin permissions
        with Session(self.browser) as session:
            make_user(session, username=user_name,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user_name, "login"))
            is_admin_role_selected = self.user.admin_role_to_user(user_name)
            self.assertTrue(is_admin_role_selected)

        # FIX ME: UI doesn't authenticate user created via UI auto: Issue #1152
        # Once #1152 is fixed; need to pass user_name and password to Session
        with Session(self.browser) as session:
            # Create New organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

            # Create New Lifecycle environment1
            make_lifecycle_environment(session, org=org_name, name=env_1_name)
            self.assertTrue(self.contentenv.wait_until_element
                            (common_locators["alert.success"]))
            # Create New  Lifecycle environment2
            make_lifecycle_environment(session, org=org_name, name=env_2_name,
                                       prior=env_1_name)
            self.assertTrue(self.contentenv.wait_until_element
                            (common_locators["alert.success"]))

            # Create custom product
            make_product(session, org=org_name,
                         name=product_name)
            self.assertIsNotNone(self.products.search(product_name))

            # Create a YUM repository
            make_repository(session, org=org_name, name=yum_repository_name,
                            product=product_name, url=GOOGLE_CHROME_REPO)
            self.assertIsNotNone(self.repository.search(yum_repository_name))

            # Create a puppet Repository
            make_repository(session, org=org_name, name=puppet_repository_name,
                            product=product_name, url=FAKE_0_PUPPET_REPO,
                            repo_type=REPO_TYPE['puppet'])
            self.assertIsNotNone(self.repository.search
                                 (puppet_repository_name))

            # Sync YUM and puppet repository
            self.navigator.go_to_sync_status()
            sync = self.sync.sync_custom_repos(product_name,
                                               [yum_repository_name,
                                                puppet_repository_name])
            self.assertIsNotNone(sync)

            # Create new content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))

            # Add YUM repository to content-view
            self.content_views.add_remove_repos(cv_name, [yum_repository_name])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            # Add puppet-module to content-view
            self.content_views.add_puppet_module(cv_name, puppet_module,
                                                 filter_term=module_ver)

            # Publish content-view
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

            # Promote content-view to life-cycle environment 1
            self.content_views.promote(cv_name, version="Version 1",
                                       env=env_1_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

            # Promote content-view to life-cycle environment 2
            self.content_views.promote(cv_name, version="Version 1",
                                       env=env_2_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

            # Create a new libvirt compute resource
            make_resource(session, org=org_name, name=compute_resource_name,
                          provider_type=provider_type, url=url)
            self.assertIsNotNone(self.compute_resource.search
                                 (compute_resource_name))

            # Create a subnet
            make_subnet(session, org=org_name, subnet_name=subnet_name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask="255.255.255.0")
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name))

            # Create a Domain
            make_domain(session, org=org_name, name=domain,
                        description=description)
            self.assertIsNotNone(self.domain.search(description))

            # Create a HostGroup
            make_hostgroup(session, name=hostgroup_name)
            self.assertIsNotNone(self.hostgroup.search(hostgroup_name))

    def test_end_to_end(self):
        """@Test: Perform end to end smoke tests using RH repos.

        @Feature: Smoke test

        @Assert: All tests should succeed and Content should be successfully
        fetched by client

        """
        org_name = gen_string("alpha", 6)
        cv_name = gen_string("alpha", 6)
        activation_key_name = gen_string("alpha", 6)
        env_name = gen_string("alpha", 6)
        server_name = conf.properties['main.server.hostname']
        product_name = "Red Hat Employee Subscription"
        repo_names = [
            "Red Hat Enterprise Virtualization Agents for RHEL 6 Server "
            "RPMs x86_64 6.5",
            "Red Hat Enterprise Virtualization Agents for RHEL 6 Server "
            "RPMs x86_64 6Server",
        ]
        repos = self.sync.create_repos_tree(RHVA_REPO_TREE)
        package_name = "python-kitchen"
        cloned_manifest_path = manifests.clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(cloned_manifest_path, remote_file=cloned_manifest_path)
        with Session(self.browser) as session:
            # Create New organization
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            # Create New Lifecycle environment
            make_lifecycle_environment(session, org=org_name, name=env_name)
            self.assertIsNotNone(
                self.contentenv.wait_until_element(
                    common_locators["alert.success"]))
            # Navigate UI to select org and redhat subscription page
            session.nav.go_to_select_org(org_name)
            session.nav.go_to_red_hat_subscriptions()
            # Upload manifest from webui
            self.subscriptions.upload(cloned_manifest_path)
            self.assertTrue(
                session.nav.wait_until_element(
                    common_locators['alert.success']))
            session.nav.go_to_red_hat_repositories()
            # List of dictionary passed to enable the redhat repos
            # It selects Product->Reposet-> Repo
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            # Sync the repos
            sync = self.sync.sync_rh_repos(repos)
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(sync)
            # Create new content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add YUM repository to content-view
            self.content_views.add_remove_repos(cv_name, repo_names)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators["alert.success"]))
            # Publish content-view
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators["alert.success"]))

            # Promote content-view to life-cycle environment 1
            self.content_views.promote(cv_name, version="Version 1",
                                       env=env_name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators["alert.success"]))
            # Create Activation-Key
            make_activationkey(
                session, org=org_name, name=activation_key_name, env=env_name,
                content_view=cv_name)
            self.activationkey.associate_product(
                activation_key_name, [product_name]
            )
            self.assertIsNotNone(
                self.activationkey.wait_until_element(
                    common_locators["alert.success"]))
            # Create VM
            with VirtualMachine(distro='rhel65') as vm:
                # Install rpm
                result = vm.run(
                    'rpm -i http://{0}/pub/katello-ca-consumer-'
                    '{0}-1.0-1.noarch.rpm'.format(server_name)
                )
                self.assertEqual(
                    result.return_code, 0,
                    "failed to install katello-ca-consumer rpm"
                )
                # Register client with foreman server using activation-key
                result = vm.run(
                    'subscription-manager register --activationkey {0} '
                    '--org {1} --force'
                    .format(activation_key_name, org_name)
                )
                self.assertEqual(
                    result.return_code, 0,
                    "failed to register client"
                )
                # Install contents from sat6 server
                result = vm.run('yum install -y {0}'.format(package_name))
                self.assertEqual(
                    result.return_code, 0,
                    "Package install failed"
                )
                # Verify if package is installed by query it
                result = vm.run('rpm -q {0}'.format(package_name))
                self.assertIn(package_name, result.stdout[0])
