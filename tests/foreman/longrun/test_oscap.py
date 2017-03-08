"""Tests for the Oscap report upload feature

:Requirement: Oscap

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.api.utils import configure_puppet_test
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier4,
    skip_if_bug_open,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context, make_hostgroup, make_oscappolicy
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class OpenScapTestCase(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        """ Create an organization, environment, content view and activation key.

        1. Create new organization and environment
        2. Clone and upload manifest
        3. Sync a RedHat repository
        4. Create content-view
        5. Add repository to content-view
        6. Promote/publish content-view
        7. Create an activation-key
        8. Add product to activation-key
        """
        super(OpenScapTestCase, cls).setUpClass()
        cls.config_env = configure_puppet_test()

    @run_only_on('sat')
    @tier4
    def test_positive_upload_to_satellite(self):
        """Perform end to end oscap test and upload reports.

        :id: 17a0978d-64f9-44ad-8303-1f54ada08602

        :Assert: Oscap reports from rhel6 and rhel7 clients should be uploaded
            to satellite6 and be searchable.

        :CaseLevel: System
        """
        if settings.rhel6_repo is None:
            self.skipTest('Missing configuration for rhel6_repo')
        rhel6_repo = settings.rhel6_repo
        if settings.rhel7_repo is None:
            self.skipTest('Missing configuration for rhel7_repo')
        rhel7_repo = settings.rhel7_repo
        rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
        rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        hgrp6_name = gen_string('alpha')
        hgrp7_name = gen_string('alpha')
        policy_values = [
            {
                'content': rhel6_content,
                'hgrp': hgrp6_name,
                'policy': gen_string('alpha'),
            },
            {
                'content': rhel7_content,
                'hgrp': hgrp7_name,
                'policy': gen_string('alpha'),
            },
        ]
        vm_values = [
            {
                'distro': DISTRO_RHEL6,
                'hgrp': hgrp6_name,
                'rhel_repo': rhel6_repo,
            },
            {
                'distro': DISTRO_RHEL7,
                'hgrp': hgrp7_name,
                'rhel_repo': rhel7_repo,
            },
        ]
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            # Creates oscap content for both rhel6 and rhel7
            for content in [rhel6_content, rhel7_content]:
                session.nav.go_to_oscap_content()
                self.oscapcontent.update(
                    content,
                    content_org=self.config_env['org_name']
                )
            set_context(session, org=self.config_env['org_name'])
            # Creates host_group for both rhel6 and rhel7
            for host_group in [hgrp6_name, hgrp7_name]:
                make_hostgroup(
                    session,
                    content_source=self.config_env['sat6_hostname'],
                    name=host_group,
                    puppet_ca=self.config_env['sat6_hostname'],
                    puppet_master=self.config_env['sat6_hostname'],
                )
            # Creates oscap_policy for both rhel6 and rhel7.
            for value in policy_values:
                make_oscappolicy(
                    session,
                    content=value['content'],
                    host_group=value['hgrp'],
                    name=value['policy'],
                    period=OSCAP_PERIOD['weekly'],
                    profile=OSCAP_PROFILE['common'],
                    period_value=OSCAP_WEEKDAY['friday'],
                )
            # Creates two vm's each for rhel6 and rhel7, runs
            # openscap scan and uploads report to satellite6.
            for value in vm_values:
                with VirtualMachine(distro=value['distro']) as vm:
                    host = vm.hostname
                    vm.install_katello_ca()
                    vm.register_contenthost(
                        self.config_env['org_name'],
                        self.config_env['ak_name']
                    )
                    vm.configure_puppet(value['rhel_repo'])
                    self.hosts.update(
                        name=vm._target_image,
                        domain_name=vm._domain,
                        parameters_list=[
                            ['Host', 'Lifecycle Environment',
                             self.config_env['env_name']],
                            ['Host', 'Content View',
                             self.config_env['cv_name']],
                            ['Host', 'Host Group', value['hgrp']],
                            ['Host', 'Reset Puppet Environment', True],
                        ],
                    )
                    session.nav.go_to_hosts()
                    # Run "puppet agent -t" twice so that it detects it's,
                    # satellite6 and fetch katello SSL certs.
                    for _ in range(2):
                        vm.run(u'puppet agent -t 2> /dev/null')
                    result = vm.run(
                        u'cat /etc/foreman_scap_client/config.yaml'
                        '| grep profile'
                    )
                    self.assertEqual(result.return_code, 0)
                    # Runs the actual oscap scan on the vm/clients and
                    # uploads report to Internal Capsule.
                    vm.execute_foreman_scap_client()
                    # Assert whether oscap reports are uploaded to
                    # Satellite6.
                    self.assertTrue(self.oscapreports.search(host))

    @skip_if_bug_open('bugzilla', 1420439)
    @tier4
    def test_positive_push_updated_content(self):
        """Perform end to end oscap test, and push the updated scap content
         after first run.

        :id: 7eb75ca5-2ea1-434e-bb43-1223fa4d8e9f

        :Assert: Satellite should push updated content to Clients and satellite
            should get updated reports

        :CaseLevel: System
        """
        if settings.rhel7_repo is None:
            self.skipTest('Missing configuration for rhel7_repo')
        rhel7_repo = settings.rhel7_repo
        rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        content_update = OSCAP_DEFAULT_CONTENT['rhel_firefox']
        hgrp7_name = gen_string('alpha')
        policy_values = {
            'content': rhel7_content,
            'hgrp': hgrp7_name,
            'policy': gen_string('alpha'),
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            # Creates oscap content for rhel7
            session.nav.go_to_oscap_content()
            self.oscapcontent.update(
                rhel7_content,
                content_org=self.config_env['org_name']
            )
            self.oscapcontent.update(
                content_update,
                content_org=self.config_env['org_name']
            )
            set_context(session, org=self.config_env['org_name'])
            # Creates host_group for rhel7
            make_hostgroup(
                session,
                content_source=self.config_env['sat6_hostname'],
                name=hgrp7_name,
                puppet_ca=self.config_env['sat6_hostname'],
                puppet_master=self.config_env['sat6_hostname'],
            )
            # Creates oscap_policy for both rhel6 and rhel7.
            make_oscappolicy(
                session,
                content=policy_values.get('content'),
                host_group=policy_values.get('hgrp'),
                name=policy_values.get('policy'),
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['common'],
                period_value=OSCAP_WEEKDAY['friday'],
            )
            # Creates two vm's each for rhel6 and rhel7, runs
            # openscap scan and uploads report to satellite6.
            with VirtualMachine(distro=vm_values.get('distro')) as vm:
                host = vm.hostname
                vm.install_katello_ca()
                vm.register_contenthost(
                    self.config_env['org_name'],
                    self.config_env['ak_name']
                )
                vm.configure_puppet(vm_values.get('rhel_repo'))
                self.hosts.update(
                    name=vm._target_image,
                    domain_name=vm._domain,
                    parameters_list=[
                        ['Host', 'Lifecycle Environment',
                         self.config_env['env_name']],
                        ['Host', 'Content View', self.config_env['cv_name']],
                        ['Host', 'Host Group', vm_values.get('hgrp')],
                        ['Host', 'Reset Puppet Environment', True],
                    ],
                )
                # Run "puppet agent -t" twice so that it detects it's,
                # satellite6 and fetch katello SSL certs.
                for _ in range(2):
                    vm.run(u'puppet agent -t 2> /dev/null')
                result = vm.run(
                    u'cat /etc/foreman_scap_client/config.yaml'
                    '| grep content_path'
                )
                self.assertEqual(result.return_code, 0)
                # Runs the actual oscap scan on the vm/clients and
                # uploads report to Internal Capsule.
                vm.execute_foreman_scap_client()
                # Assert whether oscap reports are uploaded to
                # Satellite6.
                self.assertTrue(self.oscapreports.search(host))
                self.oscappolicy.update(
                    name=policy_values.get('policy'),
                    new_name=gen_string('alpha'),
                    content=OSCAP_DEFAULT_CONTENT['rhel_firefox'],
                    profile=OSCAP_PROFILE['firefox'],
                    period=OSCAP_PERIOD['weekly'],
                    period_value=OSCAP_WEEKDAY['friday'],
                )
                self.oscapreports.delete(host, really=True)
                for _ in range(2):
                    vm.run(u'puppet agent -t 2> /dev/null')
                updated_result = vm.run(
                    u'cat /etc/foreman_scap_client/config.yaml'
                    '| grep content_path'
                )
                self.assertIsNot(result, updated_result)
                self.assertEqual(updated_result.return_code, 0)
                # Runs the actual oscap scan on the vm/clients and
                # uploads report to Internal Capsule.
                vm.execute_foreman_scap_client()
                self.assertTrue(self.oscapreports.search(host))

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_has_arf_report_summary_page(self):
        """OSCAP ARF Report now has summary page

        :id: 25be7898-50c5-4825-adc7-978c7b4e3488

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :Assert: Oscap ARF reports should have summary page.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_view_full_report_button(self):
        """'View full Report' button should exist for OSCAP Reports.

        :id: 5a41916d-66db-4d2f-8261-b83f833189b9

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :Assert: Should have 'view full report' button to view the actual HTML
            report.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_download_xml_button(self):
        """'Download xml' button should exist for OSCAP Reports
        to be downloaded in xml format.

        :id: 07a5f495-a702-4ca4-b5a4-579a133f9181

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :Assert: Should have 'Download xml in bzip' button to download the xml
            report.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_select_oscap_proxy(self):
        """Oscap-Proxy select box should exist while filling hosts
        and host-groups form.

        :id: d56576c8-6fab-4af6-91c1-6a56d9cca94b

        :Steps: Choose the Oscap Proxy/capsule appropriately for the host or
            host-groups.

        :Assert: Should have an Oscap-Proxy select box while filling hosts and
            host-groups form.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_delete_multiple_arf_reports(self):
        """Multiple arf reports deletion should be possible.

        :id: c1a8ce02-f42f-4c48-893d-8f31432b5520

        :Steps:
            1. Run Oscap scans are run for multiple Hosts.
            2. Make sure the oscap reports with it's corresponding hostnames
               are visible in the UI.
            3. Now select multiple reports from the checkbox and delete the
               reports.

        :Assert: Multiple Oscap ARF reports can be deleted.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_reporting_emails_of_oscap_reports(self):
        """Email Reporting of oscap reports should be possible.

        :id: 003d4d28-f694-4e54-a149-247f58298ecc

        :Assert: Whether email reporting of oscap reports is possible.

        :caseautomation: notautomated

        :CaseLevel: System
        """
