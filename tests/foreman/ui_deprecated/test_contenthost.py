# -*- encoding: utf-8 -*-
"""Test class for Content Hosts UI

:Requirement: Content Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer, gen_string
from six.moves.urllib.parse import urljoin
from nailgun import entities

from robottelo.cleanup import setting_cleanup, vm_cleanup
from robottelo.cli.factory import (
    make_virt_who_config,
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
    virt_who_hypervisor_config,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DISTRO_RHEL7,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_YUM_REPO,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    VDC_SUBSCRIPTION_NAME,
    VIRT_WHO_HYPERVISOR_TYPES,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class ContentHostTestCase(UITestCase):
    """Implements Content Host tests in UI"""

    @classmethod
    def set_session_org(cls):
        """Create an organization for tests, which will be selected
        automatically"""
        cls.session_org = entities.Organization().create()

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Lifecycle Environment, Content View and Activation key
        """
        super(ContentHostTestCase, cls).setUpClass()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.session_org).create()
        cls.content_view = entities.ContentView(
            organization=cls.session_org).create()
        cls.activation_key = entities.ActivationKey(
            environment=cls.env,
            organization=cls.session_org,
        ).create()
        setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        }, force_manifest_upload=True)
        setup_org_for_a_custom_repo({
            'url': FAKE_1_YUM_REPO,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })
        setup_org_for_a_custom_repo({
            'url': FAKE_6_YUM_REPO,
            'organization-id': cls.session_org.id,
            'content-view-id': cls.content_view.id,
            'lifecycle-environment-id': cls.env.id,
            'activationkey-id': cls.activation_key.id,
        })

    def setUp(self):
        """Create a VM, subscribe it to satellite-tools repo, install
        katello-ca and katello-agent packages"""
        super(ContentHostTestCase, self).setUp()
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.addCleanup(vm_cleanup, self.client)
        self.client.create()
        self.client.install_katello_ca()
        self.client.register_contenthost(
            self.session_org.label, self.activation_key.name)
        self.assertTrue(self.client.subscribed)
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    @skip_if_bug_open('bugzilla', 1495271)
    @tier3
    def test_positive_search_by_subscription_status(self):
        """Register host into the system and search for it afterwards by
        subscription status

        :id: b4d24ee7-51b9-43e4-b0c9-7866b6340ce1

        :expectedresults: Validate that host can be found for valid
            subscription status and that host is not present in the list for
            invalid status

        :BZ: 1406855, 1498827

        :CaseLevel: System
        """
        with Session(self):
            self.assertIsNotNone(self.contenthost.search(self.client.hostname))
            self.assertIsNotNone(
                self.contenthost.search(
                    self.client.hostname,
                    _raw_query='subscription_status = valid',
                )
            )
            self.assertIsNone(
                self.contenthost.search(
                    self.client.hostname,
                    _raw_query='subscription_status != valid',
                )
            )

    @tier3
    def test_positive_sort_by_last_checkin(self):
        """Register two content hosts and then sort them by last checkin date

        :id: c42c1347-8b3a-4ba7-95d1-609e2e9ec40e

        :customerscenario: true

        :expectedresults: Validate that content hosts are sorted properly

        :BZ: 1281251

        :CaseLevel: System
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(
                self.session_org.label, self.activation_key.name)
            self.assertTrue(vm.subscribed)
            vm.enable_repo(REPOS['rhst7']['id'])
            vm.install_katello_agent()
            with Session(self):
                self.assertIsNotNone(
                    self.contenthost.search(self.client.hostname))
                if bz_bug_is_open(1495271):
                    self.dashboard.navigate_to_entity()
                self.assertIsNotNone(self.contenthost.search(vm.hostname))
                self.contenthost.click(common_locators['kt_clear_search'])
                if bz_bug_is_open(1495271):
                    self.dashboard.navigate_to_entity()
                    self.contenthost.navigate_to_entity()
                # In case we have a lot of unregistered hosts
                # fixme: Should be replaced with loop across all pages
                self.contenthost.assign_value(
                    common_locators['table_per_page'], '100')
                # prevent any issues in case some default sorting was set
                self.contenthost.sort_table_by_column('Name')
                dates = self.contenthost.sort_table_by_column('Last Checkin')
                checked_in_dates = [date for date in dates
                                    if date != 'Never checked in']
                self.assertGreater(checked_in_dates[1], checked_in_dates[0])
                dates = self.contenthost.sort_table_by_column('Last Checkin')
                self.assertGreater(dates[0], dates[1])

    @tier3
    def test_positive_install_package(self):
        """Install a package to a host remotely

        :id: 13b9422d-4b7a-4068-9a57-a94602cd6410

        :expectedresults: Package was successfully installed

        :CaseLevel: System
        """
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Install',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_0_CUSTOM_PACKAGE_NAME))

    @tier3
    def test_negative_install_package(self):
        """Attempt to install non-existent package to a host remotely

        :id: d60b70f9-c43f-49c0-ae9f-187ffa45ac97

        :customerscenario: true

        :BZ: 1262940

        :expectedresults: Task finished with warning

        :CaseLevel: System
        """
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Install',
                gen_string('alphanumeric'),
            )
            self.assertEqual(result, 'warning')

    @tier3
    def test_positive_remove_package(self):
        """Remove a package from a host remotely

        :id: 86d8896b-06d9-4c99-937e-f3aa07b4eb69

        :expectedresults: Package was successfully removed

        :CaseLevel: System
        """
        self.client.download_install_rpm(
            FAKE_6_YUM_REPO,
            FAKE_0_CUSTOM_PACKAGE
        )
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Remove',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNone(self.contenthost.package_search(
                self.client.hostname, FAKE_0_CUSTOM_PACKAGE_NAME))

    @tier3
    def test_positive_upgrade_package(self):
        """Upgrade a host package remotely

        :id: 1969db93-e7af-4f5f-973d-23c222224db6

        :expectedresults: Package was successfully upgraded

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Package Update',
                FAKE_1_CUSTOM_PACKAGE_NAME,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier3
    @upgrade
    def test_positive_install_package_group(self):
        """Install a package group to a host remotely

        :id: a43fb21b-5f6a-4f14-8cd6-114ec287540c

        :expectedresults: Package group was successfully installed

        :CaseLevel: System
        """
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Install',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self.assertIsNotNone(self.contenthost.package_search(
                    self.client.hostname, package))

    @tier3
    def test_positive_remove_package_group(self):
        """Remove a package group from a host remotely

        :id: dbeea1f2-adf4-4ad8-a989-efad8ce21b98

        :expectedresults: Package group was successfully removed

        :CaseLevel: System
        """
        with Session(self):
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Install',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            result = self.contenthost.execute_package_action(
                self.client.hostname,
                'Group Remove',
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            self.assertEqual(result, 'success')
            for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
                self.assertIsNone(self.contenthost.package_search(
                    self.client.hostname, package))

    @tier3
    @upgrade
    def test_positive_install_errata(self):
        """Install a errata to a host remotely

        :id: b69b9797-3c0c-42cd-94ed-3f751bb9b24c

        :expectedresults: Errata was successfully installed

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with Session(self):
            result = self.contenthost.install_errata(
                self.client.hostname,
                FAKE_2_ERRATA_ID,
            )
            self.assertEqual(result, 'success')
            self.assertIsNotNone(self.contenthost.package_search(
                self.client.hostname, FAKE_2_CUSTOM_PACKAGE))

    @tier3
    def test_positive_search_errata_non_admin(self):
        """Search for host's errata by non-admin user with enough permissions

        :id: 5b8887d2-987f-4bce-86a1-8f65ca7e1195

        :customerscenario: true

        :BZ: 1255515

        :expectedresults: User can access errata page and proper errata is
            listed

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        default_loc = entities.Location().search(
            query={'search': 'name="{0}"'.format(DEFAULT_LOC)})[0]
        role = entities.Role().create()
        for permission_name in (
                'view_hosts', 'view_lifecycle_environments',
                'view_content_views', 'view_organizations'):
            entities.Filter(
                permission=entities.Permission(name=permission_name).search(),
                role=role,
            ).create()
        entities.User(
            role=[role],
            admin=False,
            login=user_login,
            password=user_password,
            organization=[self.session_org],
            location=[default_loc],
            default_organization=self.session_org,
        ).create()
        with Session(self, user=user_login, password=user_password):
            result = self.contenthost.errata_search(
                self.client.hostname, FAKE_2_ERRATA_ID)
            self.assertIsNotNone(result)

    @tier3
    def test_positive_fetch_registered_by(self):
        """Register a host with activation key and fetch host's 'Registered by'
        field value.

        :id: 5c6dbb5d-bd26-4439-ab04-536a6ad012b9

        :expectedresults: 'Registered By' field on content host page points to
            activation key which was used to register the host

        :BZ: 1380117

        :CaseLevel: System
        """
        with Session(self):
            result = self.contenthost.fetch_parameters(
                self.client.hostname,
                [['Details', 'Registered By']],
            )
            self.assertEqual(
                result['Registered By'], self.activation_key.name)

    @skip_if_bug_open('bugzilla', 1351464)
    @skip_if_bug_open('bugzilla', 1387892)
    @tier3
    def test_positive_provisioning_host_link(self):
        """Check that the host link in provisioning tab of content host page
        point to the host details page.

        :id: 28f5fb0e-007b-4ee6-876e-9693fb7f5841

        :expectedresults: The Provisioning host details name link at
            content_hosts/provisioning point to host detail page eg:
            hosts/hostname

        :BZ: 1387892

        :CaseLevel: System
        """
        with Session(self):
            # open the content host
            self.contenthost.search_and_click(self.client.hostname)
            # open the provisioning tab of the content host
            self.contenthost.click(
                tab_locators['contenthost.tab_provisioning_details'])
            # click the name field value that contain the hostname
            self.contenthost.click(
                tab_locators['contenthost.tab_provisioning_details_host_link'])
            # assert that the current url is equal to:
            # server_host_url/hosts/hostname
            host_url = urljoin(settings.server.get_url(),
                               'hosts/{0}'.format(self.client.hostname))
            self.assertEqual(self.browser.current_url, host_url)

    @tier3
    @upgrade
    def test_positive_ensure_errata_applicability_with_host_reregistered(self):
        """Ensure that errata remain available to install when content host is
        re-registered

        :id: 30b1e512-45e5-481e-845f-5344ed81450d

        :customerscenario: true

        :steps:
            1. Prepare an activation key with content view that contain a
                repository with a package that has errata
            2. Register the host to activation key
            3. Install the package that has errata
            4. Refresh content host subscription running:
                "subscription-manager refresh  && yum repolist"
            5. Ensure errata is available for installation
            6. Refresh content host subscription running:
                "subscription-manager refresh  && yum repolist"

        :expectedresults: errata is available in installable errata list

        :BZ: 1463818

        :CaseLevel: System
        """
        self.client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        result = self.client.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        self.assertEqual(result.return_code, 0)
        result = self.client.run(
            'subscription-manager refresh  && yum repolist')
        self.assertEqual(result.return_code, 0)
        with Session(self):
            self.assertIsNotNone(
                self.contenthost.errata_search(
                    self.client.hostname, FAKE_2_ERRATA_ID)
            )
            result = self.client.run(
                'subscription-manager refresh  && yum repolist')
            self.assertEqual(result.return_code, 0)
            self.assertIsNotNone(
                self.contenthost.errata_search(
                    self.client.hostname, FAKE_2_ERRATA_ID)
            )

    @tier3
    @upgrade
    def test_positive_check_ignore_facts_os_setting(self):
        """Verify that 'Ignore facts for operating system' setting works
        properly

        :steps:

            1. Create a new host entry using content host self registration
               procedure
            2. Check that there is a new setting added "Ignore facts for
               operating system", and set it to true.
            3. Upload the facts that were read from initial host, but with a
               change in all the operating system fields to a different OS or
               version.
            4. Verify that the host OS isn't updated.
            5. Set the setting in step 2 to false.
            6. Upload same modified facts from step 3.
            7. Verify that the host OS is updated.
            8. Verify that new OS is created

        :id: 71bed439-105c-4e87-baae-738379d055fb

        :customerscenario: true

        :expectedresults: Host facts impact its own values properly according
            to the setting values

        :BZ: 1155704

        :CaseLevel: System
        """
        ignore_setting = entities.Setting().search(
            query={'search': 'name="ignore_facts_for_operatingsystem"'})[0]
        default_ignore_setting = str(ignore_setting.value)
        major = str(gen_integer(15, 99))
        minor = str(gen_integer(1, 9))
        expected_os = "RedHat {}.{}".format(major, minor)
        with Session(self):
            host = entities.Host().search(query={
                'search': 'name={0} and organization_id={1}'.format(
                    self.client.hostname, self.session_org.id)
            })[0].read()
            # Get host current operating system value
            os = self.hosts.get_host_properties(
                self.client.hostname, ['Operating System'])['Operating System']
            # Change necessary setting to true
            ignore_setting.value = 'True'
            ignore_setting.update({'value'})
            # Add cleanup function to roll back setting to default value
            self.addCleanup(
                setting_cleanup,
                'ignore_facts_for_operatingsystem',
                default_ignore_setting
            )
            # Read all facts for corresponding host
            facts = host.get_facts(
                data={u'per_page': 10000})['results'][self.client.hostname]
            # Modify OS facts to another values and upload them to the server
            # back
            facts['operatingsystem'] = 'RedHat'
            facts['osfamily'] = 'RedHat'
            facts['operatingsystemmajrelease'] = major
            facts['operatingsystemrelease'] = "{}.{}".format(major, minor)
            host.upload_facts(
                data={
                    u'name': self.client.hostname,
                    u'facts': facts,
                }
            )
            updated_os = self.hosts.get_host_properties(
                self.client.hostname, ['Operating System'])['Operating System']
            # Check that host OS was not changed due setting was set to true
            self.assertEqual(os, updated_os)
            # Put it to false and re-run the process
            ignore_setting.value = 'False'
            ignore_setting.update({'value'})
            host.upload_facts(
                data={
                    u'name': self.client.hostname,
                    u'facts': facts,
                }
            )
            updated_os = self.hosts.get_host_properties(
                self.client.hostname, ['Operating System'])['Operating System']
            # Check that host OS was changed to new value
            self.assertNotEqual(os, updated_os)
            self.assertEqual(updated_os, expected_os)
            # Check that new OS was created
            self.assertIsNotNone(self.operatingsys.search(
                expected_os, _raw_query=expected_os))

    @tier3
    @upgrade
    @stubbed()
    def test_positive_bulk_add_subscriptions(self):
        """Add a subscription to more than one content host, using bulk actions.

        :id: a427c77f-100d-4af5-9248-6f806db364ef

        :steps:

            1. Upload a manifest with, or use an existing, subscription
            2. Register multiple hosts to the current organization
            3. Select all of those hosts
            4. Navigate to the bulk subscriptions page
            5. Select and add a subscription to the hosts

        :expectedresults: The subscriptions are successfully attached to the
            hosts

        :CaseLevel: System
        """

    @tier3
    @stubbed()
    def test_positive_bulk_remove_subscriptions(self):
        """Remove a subscription to more than one content host, using bulk
        actions.

        :id: f74b829e-d888-4caf-a25e-ca64b073a3fc

        :steps:

            1. Upload a manifest with, or use an existing, subscription
            2. Register multiple hosts to the current organization
            3. Select all of those hosts
            4. Navigate to the bulk subscriptions page
            5. Select and add a subscription to the hosts
            6. Verify that the subscriptions were added
            7. Reselect all the hosts from step 3
            8. Navigate to the bulk subscriptions page
            9. Select the subscription added in step 5 and remove it

        :expectedresults: The subscriptions are successfully removed from the
            hosts

        :CaseLevel: System
        """

    @skip_if_not_set('clients', 'fake_manifest', 'compute_resources')
    @tier3
    @upgrade
    def test_positive_virt_who_hypervisor_subscription_status(self):
        """Check that virt-who hypervisor shows the right subscription status
        without and with attached subscription.

        :id: 8b2cc5d6-ac85-463f-a973-f4818c55fb37

        :customerscenario: true

        :expectedresults:
            1. With subscription not attached, Subscription status is
               "Unsubscribed hypervisor" and represented by a yellow icon in
               content hosts list.
            2. With attached subscription, Subscription status is
               "Fully entitled" and represented by a green icon in content
               hosts list.

        :BZ: 1336924

        :CaseLevel: System
        """
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        provisioning_server = settings.compute_resources.libvirt_hostname
        # Create a new virt-who config
        virt_who_config = make_virt_who_config({
            'organization-id': org.id,
            'hypervisor-type': VIRT_WHO_HYPERVISOR_TYPES['libvirt'],
            'hypervisor-server': 'qemu+ssh://{0}/system'.format(
                provisioning_server),
            'hypervisor-username': 'root',
        })
        # create a virtual machine to host virt-who service
        with VirtualMachine() as virt_who_vm:
            # configure virtual machine and setup virt-who service
            # do not supply subscription to attach to virt_who hypervisor
            virt_who_data = virt_who_hypervisor_config(
                virt_who_config['general-information']['id'],
                virt_who_vm,
                org_id=org.id,
                lce_id=lce.id,
                hypervisor_hostname=provisioning_server,
                configure_ssh=True,
            )
            virt_who_hypervisor_host = virt_who_data[
                'virt_who_hypervisor_host']
            with Session(self) as session:
                set_context(session, org=org.name, force_context=True)
                self.assertEqual(
                    session.contenthost.get_subscription_status_color(
                        virt_who_hypervisor_host['name']),
                    'yellow'
                )
                self.assertEqual(
                    session.contenthost.get_subscription_status_text(
                        virt_who_hypervisor_host['name']),
                    'Unsubscribed hypervisor'
                )
                session.contenthost.update(
                    virt_who_hypervisor_host['name'],
                    add_subscriptions=[VDC_SUBSCRIPTION_NAME]
                )
                self.assertEqual(
                    session.contenthost.get_subscription_status_color(
                        virt_who_hypervisor_host['name']),
                    'green'
                )
                self.assertEqual(
                    session.contenthost.get_subscription_status_text(
                        virt_who_hypervisor_host['name']),
                    'Fully entitled'
                )
