"""Test for virt-who configure API

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated


:Upstream: No
"""

from nailgun import entities

from robottelo.cli.factory import (
    make_virt_who_config,
    virt_who_hypervisor_config,
)
from robottelo.config import settings
from robottelo.constants import (
    VDC_SUBSCRIPTION_NAME,
    VIRT_WHO_HYPERVISOR_TYPES,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier4,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class VirtWhoConfigTestCase(UITestCase):
    """Implements Virt-who-configure UI tests"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_welcome_page(self):
        """
        :id: e25804fd-98cb-46bb-aa29-958ceb361292

        :steps:
            1. Verify UI Elements on welcome page

        :expectedresults:
            UI Welcome page describes the feature and includes a button
            to create the first config. The button brings the use to the
            config page

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_configurations_page(self):
        """ config page listings

        :id: fa6d5ce4-08b7-41fa-b7ab-ac5a018cf68a

        :steps:
            1. Create virt-who-configuration

        :expectedresults:
            Verify list the created configuration


        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_postitve_config_change_redeploy(self):
        """ change the config and redeploy the script.

        :id: 466d07b3-3cc7-43ef-b820-a5510b43e4dd

        :steps:
            1. Edit virt-who configuration and verify the updated shell script,
               redeploy the script

        :expectedresults:
            Verify the script correctly configures virt-who.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_virt_who_user_login(self):
        """ Verify users created by virt-who config is not able to access UI

        :id: 9a8bb27a-af91-47cc-9004-6e3497363dbb

        :steps:
            1. Create a virt-who configuration
            2. Attempt to login the UI with the user created by the
               virt-who configurator. Verify the login is blocked
            3. Attempt to login using Hammer with the user created by the
               virt-who configurator. Verify the login is blocked
            4. Attempt to click the username link displayed in related task
               details.

        :expectedresults:
            users created by virt-who config is not able to access UI
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_config_page_populated(self):
        """ verify page when populated

        :id: db6bbc68-2047-4c7d-af5b-31aee0030318

        :steps:
            1. Create multiple virt-who configurations


        :expectedresults: All configurations are listed on the config page

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_config_page_empty(self):
        """ verify page when empty

        :id: bb208160-9bd0-49ee-8971-6f71d48808fb

        :steps:
            1. Create multiple virt-who configurations
            2. Delete all configurations

        :expectedresults:
            The welcome page is shown when no configs are present.
        """


class VirtWhoConfigDashboardTestCase(UITestCase):
    """
    6. Review UI Dashboard
        - No reports
        - Out of Date
        - Up to Date
        - Latest out of date Configurations

    """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_dashboard_no_reports(self):
        """ No reports

        :id: 28720130-746b-4646-830e-bff8d735ef3c

        :steps:
            1. Create 2 virt-who configurations.
            2. Ensure there are no reports from any of the configs

        :expectedresults:
            Dashboard widget "No Reports" count is 2 (number of configs)

        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_dashboard_out_of_date(self):
        """ Out of Date

        :id: de39275f-4534-49ad-8389-f7e8b405d6b6

        :steps:
            1. Create 2 virt-who configurations.
            2. Cause virt-who reports to be out of date

        :expectedresults:
            Dashboard widget  "No Change" count is 2 (number of configs)

        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_dashboard_up_to_date(self):
        """ Up to Date

        :id: 5ac051f0-4540-46e5-ac3b-367721625ebb

        :steps:
            1. Create 2 virt-who configurations.
            2. Ensure virt-who reports are up to date.

        :expectedresults:
            Dashboard widget  "OK" count is 2 (number of configs)


        """
    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_lastest_out_of_date(self):
        """Verify dashboard widget Latest out of date Configurations

        :id: 1df6d171-df57-41ef-9443-c7bb15aab473

        :steps:
            1. Create 2 virt-who configurations.
            2. Cause virt-who reports to be out of date

        :expectedresults:
            The 2 virt-who configs are list in the latest out of date section
            of the widget.
        """


@run_in_one_thread
class VirtWhoConfigDeployedTestCase(UITestCase):
    """Implements Virt-who-config UI tests with virt-who config deployed"""

    @classmethod
    def set_session_org(cls):
        """Create global test case organization"""
        cls.session_org = entities.Organization().create()

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest', 'compute_resources')
    def setUpClass(cls):
        """setup virt-who virtual machine"""
        super(VirtWhoConfigDeployedTestCase, cls).setUpClass()
        cls.lce = entities.LifecycleEnvironment(
            organization=cls.session_org).create()
        cls.hypervisor_hostname = settings.compute_resources.libvirt_hostname
        # Create a new virt-who config
        virt_who_config = make_virt_who_config({
            'organization-id': cls.session_org.id,
            'hypervisor-type': VIRT_WHO_HYPERVISOR_TYPES['libvirt'],
            'hypervisor-server': 'qemu+ssh://{0}/system'.format(
                cls.hypervisor_hostname),
            'hypervisor-username': 'root',
        })
        cls.virt_who_vm = VirtualMachine()
        cls.virt_who_vm.create()
        # configure virtual machine and setup virt-who service
        cls.virt_who_data = virt_who_hypervisor_config(
            virt_who_config['general-information']['id'],
            cls.virt_who_vm,
            org_id=cls.session_org.id,
            lce_id=cls.lce.id,
            hypervisor_hostname=cls.hypervisor_hostname,
            configure_ssh=True,
            subscription_name=VDC_SUBSCRIPTION_NAME,
        )
        cls.virt_who_hypervisor_host = entities.Host(
            id=cls.virt_who_data['virt_who_hypervisor_host']['id']).read()

    @classmethod
    def tearDownClass(cls):
        """destroy the virt-who virtual machine"""
        cls.virt_who_vm.destroy()
        super(VirtWhoConfigDeployedTestCase, cls).tearDownClass()

    @tier4
    def test_positive_search_by_hypervisor(self):
        """Able to find hypervisor or not hypervisor content host by searching
        hypervisor = true or hypervisor = false

        :id: 2165023f-7184-400c-a9d9-e0c0d065a7d2

        :customerscenario: true

        :expectedresults: the hypervisor search work properly

        :BZ: 1246554, 1495271

        :CaseLevel: System
        """
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            is_hypervisor_hosts = {
                True: self.virt_who_hypervisor_host.name,
                False: self.virt_who_vm.hostname
            }
            for is_hypervisor in is_hypervisor_hosts:
                if bz_bug_is_open(1495271):
                    session.dashboard.navigate_to_entity()
                self.assertIsNotNone(
                    session.contenthost.search(
                        is_hypervisor_hosts[is_hypervisor],
                        _raw_query='hypervisor = {0}'.format(
                            str(is_hypervisor).lower())
                    )
                )
                self.assertIsNone(
                    session.subscriptions.wait_until_element(
                        locators['contenthost.select_name'] %
                        is_hypervisor_hosts[not is_hypervisor]
                    )
                )

    @skip_if_bug_open('bugzilla', 1487317)
    @skip_if_bug_open('bugzilla', 1382090)
    @tier4
    def test_positive_open_hypervisor_contenthost_from_subscription(self):
        """Open hypervisor contenthost from guests subscription link

        :id: 7279ecdc-db19-4af4-8c0b-25e696946092

        :customerscenario: true

        :expectedresults: hypervisor contenthost page opened successfully

        :BZ: 1382090, 1506636, 1487317

        :CaseLevel: System
        """
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            # ensure hypervisor content host exists and have VDC subscription
            # assigned
            session.contenthost.search_and_click(
                self.virt_who_hypervisor_host.name)
            self.contenthost.click(
                tab_locators['contenthost.tab_subscriptions'])
            self.contenthost.click(
                tab_locators['contenthost.tab_subscriptions_subscriptions']
            )
            self.assertIsNotNone(
                session.contenthost.wait_until_element(
                    locators['contenthost.subscription_select']
                    % VDC_SUBSCRIPTION_NAME)
            )
            # click the guests subscription hypervisor link
            session.subscriptions.search(VDC_SUBSCRIPTION_NAME)
            session.subscriptions.click(
                locators['subs.guests_of_hypervisor_link'] %
                (VDC_SUBSCRIPTION_NAME, self.virt_who_hypervisor_host.name)
            )
            # ensure the hypervisor contenthost page opened
            self.assertIsNotNone(
                session.contenthost.wait_until_element(
                    locators["contenthost.title"] %
                    self.virt_who_hypervisor_host.name
                )
            )
            self.assertIsNotNone(
                session.contenthost.wait_until_element(
                    tab_locators['contenthost.tab_details']
                )
            )

    @skip_if_bug_open('bugzilla', 1487317)
    @tier4
    @upgrade
    def test_positive_vdc_subscription_contenthost_association(self):
        """Ensure vdc subscription hosts association is not empty and virt-who
        hypervisor is in the association list

        :id: 3b0f5795-7c31-4bd0-aecf-41a536f9d5a2

        :customerscenario: true

        :expectedresults:
            1. subscription hosts association is not empty
            2. virt-who hypervisor is in the association list

        :BZ: 1426403, 1506636, 1487317

        :CaseLevel: System
        """
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.assertIsNotNone(
                session.contenthost.search(self.virt_who_hypervisor_host.name))
            session.subscriptions.search_and_click(VDC_SUBSCRIPTION_NAME)
            session.subscriptions.click(tab_locators['subs.sub.associations'])
            session.subscriptions.click(
                tab_locators['subs.sub.associations.hosts'])
            self.assertGreater(
                len(session.subscriptions.find_elements(
                    locators['subs.sub.associations.attached_hosts'])),
                0
            )
            self.assertIsNotNone(
                session.subscriptions.wait_until_element(
                    locators['subs.sub.associations.attached_host'] %
                    self.virt_who_hypervisor_host.name
                )
            )
