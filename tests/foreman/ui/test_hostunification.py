# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

:Requirement: Hostunification

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.constants import (
    DEFAULT_CV,
    DEFAULT_SUBSCRIPTION_NAME,
    DISTRO_RHEL7,
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_host
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class HostContentHostUnificationTestCase(UITestCase):
    """Implements Host and Content-host Unification tests in UI"""
    # Testing notes for host/content-host unification in katello/foreman
    # Basically assuring that hosts in foreman/katello bits are joined
    # and information can be associated across both parts of product.
    #
    # Devnote:
    # (the link/join will) "Most likely an internal UUID, not something
    # fuzzy like hostname"

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(HostContentHostUnificationTestCase, cls).setUpClass()
        cls.org_ = entities.Organization().create()

    @tier3
    def test_positive_register_host_via_rhsm(self):
        """Register a pre-installed host via rhsm using credentials

        :id: 4e685241-b671-4cfd-bfaa-f44a5cf78654

        :steps:
            1.  Register a host via rhsm using credentials
            2.  View host under content hosts
            3.  View host under 'All Hosts'

        :expectedresults: Hosts registered via rhsm appears under 'All hosts'
            as well as under content-hosts.

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_.label, lce='Library')
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_.name)
                self.assertIsNotNone(self.hosts.search(vm.hostname))
                self.assertIsNotNone(self.contenthost.search(vm.hostname))

    @run_in_one_thread
    @tier3
    @upgrade
    def test_positive_register_host_via_ak(self):
        """Register a pre-installed host via rhsm using activation-key

        :id: b42a1a13-49ef-418e-bb66-12ed71cf3038

        :steps:
            1.  Register a host via rhsm using activation-key
            2.  View host under content hosts
            3.  View host under 'All Hosts'

        :expectedresults: Hosts registered via activation key appears under
            'All hosts' as well as under content-hosts

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, activation_key.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                self.assertIsNotNone(self.hosts.search(vm.hostname))
                self.assertIsNotNone(self.contenthost.search(vm.hostname))

    @tier3
    @upgrade
    def test_positive_provision_foreman_host(self):
        """Test if a foreman host can be provisioned

        :id: 985b4432-4d99-43a7-a304-1b93760257dd

        :steps:

            1.  Provision a host via foreman
            2.  View host under content hosts
            3.  View host under 'All Hosts'

        :expectedresults: Hosts provisioned via foreman should appear under
            'All hosts' as well as under content-hosts.

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            hostname = u'{0}.{1}'.format(host.name, host.domain.name)
            self.assertIsNotNone(self.contenthost.search(hostname))
            self.assertIsNotNone(self.hosts.search(hostname))

    @stubbed('unstub once os/browser/env combination is changed')
    @tier3
    def test_positive_rename_foreman_host(self):
        """Hosts renamed in foreman appears in katello under content-hosts

        :id: 24182edc-8bff-46a1-b158-bcc7a3615166

        :steps:
            1.  Rename a host from 'All Hosts' page
            2.  View host under content-hosts page
            3.  View host under 'All Hosts'

        :expectedresults: Host appears in both places despite being renamed

        :BZ: 1495271

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_.label, lce='Library')
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_.name)
                name, domain_name = vm.hostname.split('.', 1)
                new_name = gen_string('alphanumeric').lower()
                self.hosts.update(
                    name,
                    domain_name,
                    new_name=new_name,
                )
                # Host rename operation is not atomic and may take some time
                for _ in range(3):
                    searched = self.hosts.search(vm.hostname)
                    if not searched:
                        break
                else:
                    self.fail('Host was not renamed')
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.hosts.search(new_name))
                self.assertIsNone(self.contenthost.search(vm.hostname))
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.contenthost.search(new_name))

    @tier3
    def test_positive_rename_content_host(self):
        """Hosts renamed in katello via content-hosts appear in foreman

        :id: 34a2c507-b992-46fa-81d9-e4b31ffd9706

        :steps:
            1.  Rename a host from 'Content-hosts' page
            2.  View host under content-hosts
            3.  View host under 'All Hosts'

        :expectedresults: Host appears in both places despite being renamed

        :BZ: 1495271

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_.label, lce='Library')
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_.name)
                new_name = gen_string('alphanumeric').lower()
                self.contenthost.update(
                    vm.hostname,
                    new_name=new_name,
                )
                self.assertIsNone(self.contenthost.search(vm.hostname))
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.contenthost.search(new_name))
                self.assertIsNone(self.hosts.search(vm.hostname))
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.hosts.search(new_name))

    @tier3
    def test_positive_rename_content_host_cli(self):
        """Content Hosts renamed in UI affects entity in the application
        entirely, so name looks different through CLI too

        :id: a64c7815-269b-45d0-9032-38df550d6cd9

        :steps:
            1.  Rename a host from 'Content-hosts' page
            2.  View host under content-hosts
            3.  View host using command line interface

        :expectedresults: Host changed its name both in UI and CLI

        :BZ: 1417953, 1495271

        :CaseLevel: System
        """
        new_name = gen_string('alphanumeric').lower()
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_.label, lce='Library')
            self.assertTrue(vm.subscribed)
            host = Host.info({'name': vm.hostname})
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_.name)
                self.contenthost.update(
                    vm.hostname,
                    new_name=new_name,
                )
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.contenthost.search(new_name))
            self.assertEqual(Host.info({'id': host['id']})['name'], new_name)

    @tier3
    def test_positive_delete_from_allhosts(self):
        """Delete a host from 'All hosts'

        :id: 896c1a7e-9292-45f2-a2b7-3d2560ae4a2d

        :steps:
            1.  Delete a host from 'All hosts' page
            2.  View host under 'Content-hosts'
            3.  View host under 'All hosts'

        :expectedresults: Host should be removed from 'All hosts' as well as
            content-hosts

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_.label, lce='Library')
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_.name)
                self.hosts.delete(vm.hostname, dropdown_present=True)
                self.assertIsNone(self.contenthost.search(vm.hostname))

    @run_in_one_thread
    @tier3
    @upgrade
    def test_positive_unregister_content_host(self):
        """Unregister a host from content-hosts page

        :id: a7d8a081-b0f2-4944-a8dc-5527cb6ab914

        :steps:
            1.  Un-register a host from content-host page
            2.  View host under content hosts
            3.  View host under 'All hosts'

        :expectedresults: Hosts un-registered from content-host should appear
            in both sides of UI

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, activation_key.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                self.contenthost.unregister(vm.hostname)
                self.contenthost.validate_subscription_status(
                    vm.hostname, False)
                self.assertIsNotNone(self.contenthost.search(vm.hostname))
                self.assertIsNotNone(self.hosts.search(vm.hostname))

    @run_in_one_thread
    @tier3
    def test_positive_delete_content_host(self):
        """Unregister and delete a host from content-hosts page

        :id: 3c75c1e6-85e3-49e6-a10e-6052a0db2b7f

        :steps:
            1.  Un-register and delete a host from content-host page
            2.  View host under content hosts
            3.  View host under 'All hosts'

        :expectedresults: Hosts un-registered from content-host should
            disappear from both sides of UI

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, activation_key.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                self.contenthost.delete(vm.hostname)
                self.assertIsNone(self.hosts.search(vm.hostname))

    @run_in_one_thread
    @tier3
    @upgrade
    def test_positive_re_register_host(self):
        """Re-register a host which was un-registered earlier from content-host

        :id: 898695dc-36ff-45b8-85be-6734e6a232d6

        :steps:
            1.  Re-register a host which was unregistered before
            2.  View host under content hosts
            3.  View host under 'All hosts'

        :expectedresults: A single entry of host should appear at both places
            on re-registering

        :CaseLevel: System
        """
        org = entities.Organization().create()
        env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        activation_key = entities.ActivationKey(
            environment=env,
            organization=org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': env.id,
            'activationkey-id': activation_key.id,
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, activation_key.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(org.name)
                self.contenthost.unregister(vm.hostname)
                self.contenthost.validate_subscription_status(
                    vm.hostname, False)
                vm.register_contenthost(org.label, activation_key.name)
                self.assertTrue(vm.subscribed)
                self.contenthost.validate_subscription_status(
                    vm.hostname, True)
                self.assertIsNotNone(self.contenthost.search(vm.hostname))
                self.assertIsNotNone(self.hosts.search(vm.hostname))

    @tier3
    def test_negative_add_subs_to_unregistered_host(self):
        """Perform a subscription action on a host which is not registered

        :id: 83ebd98e-309d-4209-bf01-0547334af5af

        :steps:
            1.  Provision a host via foreman which is not registered via rhsm
            2.  Try to add subscription from content-hosts page

        :expectedresults: User get a warning: This Host is not currently
            registered with subscription-manager.

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            hostname = u'{0}.{1}'.format(host.name, host.domain.name)
            with self.assertRaises(UIError):
                self.contenthost.update(
                    hostname,
                    add_subscriptions=[DEFAULT_SUBSCRIPTION_NAME],
                )

    @tier3
    def test_negative_add_contents_to_unregistered_host(self):
        """Perform a content action like on a host which is not registered

        :id: 67396c26-67fa-4cee-9937-65c2b9befabc

        :steps:
            1.  Provision a host via foreman which is not registered via rhsm
            2.  Try to add package from content-hosts page

        :expectedresults: User get a warning: This Host is not currently
            registered with subscription-manager.

        :CaseLevel: System
        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self) as session:
            make_host(
                session,
                name=host.name,
                org=host.organization.name,
                parameters_list=[
                    ['Host', 'Organization', host.organization.name],
                    ['Host', 'Location', host.location.name],
                    ['Host', 'Lifecycle Environment', ENVIRONMENT],
                    ['Host', 'Content View', DEFAULT_CV],
                    ['Host', 'Puppet Environment', host.environment.name],
                    [
                        'Operating System',
                        'Architecture',
                        host.architecture.name
                    ],
                    ['Operating System', 'Operating system', os_name],
                    ['Operating System', 'Media', host.medium.name],
                    ['Operating System', 'Partition table', host.ptable.name],
                    ['Operating System', 'Root password', host.root_pass],
                ],
                interface_parameters=[
                    ['Type', 'Interface'],
                    ['MAC address', host.mac],
                    ['Domain', host.domain.name],
                    ['Primary', True],
                ],
            )
            hostname = u'{0}.{1}'.format(host.name, host.domain.name)
            with self.assertRaises(UIError):
                self.contenthost.execute_package_action(
                    hostname,
                    'Package Install',
                    'busybox',
                    timeout=5,
                )
            self.contenthost.click(tab_locators['contenthost.tab_details'])
            self.assertIn(
                ('This Host is not currently registered with'
                 ' subscription-manager'),
                self.contenthost.wait_until_element(
                    locators['contenthost.subscription_message']).text
            )
