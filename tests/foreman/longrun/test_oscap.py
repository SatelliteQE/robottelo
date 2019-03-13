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
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.proxy import Proxy
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
    DEFAULT_LOC,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    skip_if_bug_open,
    tier4,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    set_context,
    make_hostgroup,
    make_oscappolicy,
    make_oscap_tailoringfile
)
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
        cls.config_env = cls.configure_puppet_test()

    @classmethod
    def configure_puppet_test(cls):
        """Sets up the whole provisioning environment needed for Puppet based
         end-to-end tests like OSCAP etc

         :returns: A dict of entities to help with provisioning
        """
        cls.rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
        cls.rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        sat6_hostname = settings.server.hostname
        ak_name_7 = gen_string('alpha')
        ak_name_6 = gen_string('alpha')
        repo_values = [
            {
                'repo': REPOS['rhst6']['name'],
                'reposet': REPOSET['rhst6'],
                'akname': ak_name_6
            },
            {
                'repo': REPOS['rhst7']['name'],
                'reposet': REPOSET['rhst7'],
                'akname': ak_name_7
            },
        ]
        # Create new organization and environment.
        org = entities.Organization(name=gen_string('alpha')).create()
        loc = entities.Location(name=DEFAULT_LOC).search()[0].read()
        puppet_env = entities.Environment().search(
            query={u'search': u'name=production'})[0].read()
        puppet_env.location.append(loc)
        puppet_env.organization.append(org)
        puppet_env = puppet_env.update(['location', 'organization'])
        Proxy.import_classes({
            u'environment': puppet_env.name,
            u'name': sat6_hostname,
        })
        env = entities.LifecycleEnvironment(
            organization=org,
            name=gen_string('alpha')
        ).create()
        # Clone and Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        # Create content view
        content_view = entities.ContentView(
            organization=org,
            name=gen_string('alpha')
        ).create()
        # Create two activation keys for rhel7 and rhel6
        for repo in repo_values:
            activation_key = entities.ActivationKey(
                name=repo.get('akname'),
                environment=env,
                organization=org,
            ).create()
            # Setup org for a RH or custom repo for RHEL6 and RHEL7
            setup_org_for_a_rh_repo({
                'product': PRDS['rhel'],
                'repository-set': repo.get('reposet'),
                'repository': repo.get('repo'),
                'organization-id': org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': env.id,
                'activationkey-id': activation_key.id,
            })
        for content in cls.rhel6_content, cls.rhel7_content:
            Scapcontent.update({
                'title': content,
                'organizations': org.name})
        return {
            'org_name': org.name,
            'cv_name': content_view.name,
            'sat6_hostname': settings.server.hostname,
            'ak_name': {'rhel7': ak_name_7, 'rhel6': ak_name_6},
            'env_name': env.name,
        }

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1479413)
    @tier4
    @upgrade
    @skip_if_not_set()
    @stubbed
    def test_positive_upload_to_satellite(self):
        """Perform end to end oscap test and upload reports.

        :id: 17a0978d-64f9-44ad-8303-1f54ada08602

        :expectedresults: Oscap reports from rhel6 and rhel7 clients should be
            uploaded to satellite6 and be searchable.

        :CaseLevel: System
        """
        if settings.rhel6_repo is None:
            self.skipTest('Missing configuration for rhel6_repo')
        rhel6_repo = settings.rhel6_repo
        if settings.rhel7_repo is None:
            self.skipTest('Missing configuration for rhel7_repo')
        rhel7_repo = settings.rhel7_repo
        hgrp6_name = gen_string('alpha')
        hgrp7_name = gen_string('alpha')
        policy6_name = gen_string('alpha')
        policy7_name = gen_string('alpha')
        policy_values = [
            {
                'content': self.rhel6_content,
                'hgrp': hgrp6_name,
                'policy': policy6_name,
            },
            {
                'content': self.rhel7_content,
                'hgrp': hgrp7_name,
                'policy': policy7_name,
            },
        ]
        vm_values = [
            {
                'distro': DISTRO_RHEL6,
                'hgrp': hgrp6_name,
                'rhel_repo': rhel6_repo,
                'policy': policy6_name,
            },
            {
                'distro': DISTRO_RHEL7,
                'hgrp': hgrp7_name,
                'rhel_repo': rhel7_repo,
                'policy': policy7_name,
            },
        ]
        with Session(self) as session:
            session.nav.go_to_select_org(self.config_env['org_name'])
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
                    host_name, _, host_domain = vm.hostname.partition('.')
                    vm.install_katello_ca()
                    vm.register_contenthost(
                        self.config_env['org_name'],
                        self.config_env['ak_name'].get(value['distro'])
                    )
                    self.assertTrue(vm.subscribed)
                    vm.configure_puppet(value['rhel_repo'])
                    self.hosts.update(
                        name=host_name,
                        domain_name=host_domain,
                        parameters_list=[
                            ['Host', 'Lifecycle Environment',
                             self.config_env['env_name']],
                            ['Host', 'Content View',
                             self.config_env['cv_name']],
                            ['Host', 'Host Group', value['hgrp']],
                            ['Host', 'Reset Puppet Environment', True],
                            ['Host', 'Openscap Capsule',
                                self.config_env['sat6_hostname']],
                        ],
                    )
                    self.hosts.update_host_bulkactions(
                        ['{0}'.format(vm.hostname.lower())],
                        action='Assign Compliance Policy',
                        parameters_list=[
                            {'policy': value['policy']}],
                    )
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

    @upgrade
    @skip_if_bug_open('bugzilla', 1420439)
    @tier4
    @stubbed
    def test_positive_push_updated_content(self):
        """Perform end to end oscap test, and push the updated scap content
         after first run.

        :id: 7eb75ca5-2ea1-434e-bb43-1223fa4d8e9f

        :expectedresults: Satellite should push updated content to Clients and
            satellite should get updated reports

        :CaseLevel: System
        """
        if settings.rhel7_repo is None:
            self.skipTest('Missing configuration for rhel7_repo')
        rhel7_repo = settings.rhel7_repo
        content_update = OSCAP_DEFAULT_CONTENT['rhel_firefox']
        hgrp7_name = gen_string('alpha')
        policy_values = {
            'content': self.rhel7_content,
            'hgrp': hgrp7_name,
            'policy': gen_string('alpha'),
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        with Session(self) as session:
            set_context(
                session, org=ANY_CONTEXT['org'], loc=ANY_CONTEXT['location'])
            self.oscapcontent.update(
                content_update,
                content_org=self.config_env['org_name']
            )
            session.nav.go_to_select_org(self.config_env['org_name'])
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
            distro_os = vm_values.get('distro')
            with VirtualMachine(distro=distro_os) as vm:
                # host = vm.hostname
                host_name, _, host_domain = vm.hostname.partition('.')
                vm.install_katello_ca()
                vm.register_contenthost(
                    self.config_env['org_name'],
                    self.config_env['ak_name'].get(distro_os)
                )
                self.assertTrue(vm.subscribed)
                vm.configure_puppet(vm_values.get('rhel_repo'))

                self.hosts.update(
                    name=host_name,
                    domain_name=host_domain,
                    parameters_list=[
                        ['Host', 'Host Group', vm_values.get('hgrp')],
                        ['Host', 'Lifecycle Environment',
                            self.config_env['env_name']],
                        ['Host', 'Content View', self.config_env['cv_name']],
                        ['Host', 'Reset Puppet Environment', True],
                        ['Host', 'Openscap Capsule',
                            self.config_env['sat6_hostname']],
                    ],
                )
                self.hosts.update_host_bulkactions(
                    ['{0}'.format(vm.hostname.lower())],
                    action='Assign Compliance Policy',
                    parameters_list=[
                        {'policy': policy_values.get('policy')}],
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
                self.assertTrue(self.oscapreports.search(vm.hostname.lower()))
                session.nav.go_to_oscap_policy()
                self.oscappolicy.update(
                    name=policy_values.get('policy'),
                    new_name=gen_string('alpha'),
                    content=OSCAP_DEFAULT_CONTENT['rhel_firefox'],
                    profile=OSCAP_PROFILE['firefox'],
                    period=OSCAP_PERIOD['weekly'],
                    period_value=OSCAP_WEEKDAY['friday'],
                )
                self.oscapreports.delete(vm.hostname.lower(), really=True)
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
                self.assertTrue(self.oscapreports.search(vm.hostname.lower()))

    @upgrade
    @run_only_on('sat')
    @tier4
    @stubbed
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule

        :id: 346946ad-4f62-400e-9390-81817006048c

        :setup: scap content, scap policy, tailoring file, host group

        :steps:

            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Create a scap policy
            4. Associate scap content with it's tailoring file
            5. Associate the policy with a hostgroup
            6. Provision a host using the hostgroup
            7. Puppet should configure and fetch the scap content
               and tailoring file

        :expectedresults: ARF report should be sent to satellite reflecting
                         the changes done via tailoring files

        :CaseImportance: Critical
        """
        if settings.rhel7_repo is None:
            self.skipTest('Missing configuration for rhel7_repo')
        rhel7_repo = settings.rhel7_repo
        hgrp7_name = gen_string('alpha')
        policy_values = {
            'content': self.rhel7_content,
            'hgrp': hgrp7_name,
            'policy': gen_string('alpha'),
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        tailoring_file_name = gen_string('alpha')
        tailoring_path = get_data_file(settings.oscap.tailoring_path)
        with Session(self) as session:
            session.nav.go_to_select_org(self.config_env['org_name'])
            # Creates host_group for rhel7
            make_hostgroup(
                session,
                content_source=self.config_env['sat6_hostname'],
                name=hgrp7_name,
                puppet_ca=self.config_env['sat6_hostname'],
                puppet_master=self.config_env['sat6_hostname'],
            )
            make_oscap_tailoringfile(
                session,
                name=tailoring_file_name,
                tailoring_path=tailoring_path,
            )
            self.assertIsNotNone(
                self.oscaptailoringfile.search(tailoring_file_name))
            # Creates oscap_policy for rhel7.
            make_oscappolicy(
                session,
                content=policy_values.get('content'),
                host_group=policy_values.get('hgrp'),
                name=policy_values.get('policy'),
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['common'],
                period_value=OSCAP_WEEKDAY['friday'],
                tailoring=tailoring_file_name,
                tailoring_profile=OSCAP_PROFILE['tailoring_rhel7']
            )
            distro_os = vm_values.get('distro')
            with VirtualMachine(distro=distro_os) as vm:
                host_name, _, host_domain = vm.hostname.partition('.')
                vm.install_katello_ca()
                vm.register_contenthost(
                    self.config_env['org_name'],
                    self.config_env['ak_name'].get(distro_os)
                )
                self.assertTrue(vm.subscribed)
                vm.configure_puppet(rhel7_repo)
                self.hosts.update(
                    name=host_name,
                    domain_name=host_domain,
                    parameters_list=[
                        ['Host', 'Host Group', vm_values.get('hgrp')],
                        ['Host', 'Lifecycle Environment',
                            self.config_env['env_name']],
                        ['Host', 'Content View', self.config_env['cv_name']],
                        ['Host', 'Reset Puppet Environment', True],
                        ['Host', 'Openscap Capsule',
                            self.config_env['sat6_hostname']],
                    ],
                )
                self.hosts.update_host_bulkactions(
                    ['{0}'.format(vm.hostname.lower())],
                    action='Assign Compliance Policy',
                    parameters_list=[
                        {'policy': policy_values.get('policy')}],
                )
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
                self.assertTrue(self.oscapreports.search(
                    '{0}'.format(vm.hostname)))

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_has_arf_report_summary_page(self):
        """OSCAP ARF Report now has summary page

        :id: 25be7898-50c5-4825-adc7-978c7b4e3488

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :expectedresults: Oscap ARF reports should have summary page.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_view_full_report_button(self):
        """'View full Report' button should exist for OSCAP Reports.

        :id: 5a41916d-66db-4d2f-8261-b83f833189b9

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :expectedresults: Should have 'view full report' button to view the
            actual HTML report.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_download_xml_button(self):
        """'Download xml' button should exist for OSCAP Reports
        to be downloaded in xml format.

        :id: 07a5f495-a702-4ca4-b5a4-579a133f9181

        :Steps:
            1. Make sure the oscap report with it's corresponding hostname
               is visible in the UI.
            2. Click on the host name to access the oscap report.

        :expectedresults: Should have 'Download xml in bzip' button to download
            the xml report.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_select_oscap_proxy(self):
        """Oscap-Proxy select box should exist while filling hosts
        and host-groups form.

        :id: d56576c8-6fab-4af6-91c1-6a56d9cca94b

        :Steps: Choose the Oscap Proxy/capsule appropriately for the host or
            host-groups.

        :expectedresults: Should have an Oscap-Proxy select box while filling
            hosts and host-groups form.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
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

        :expectedresults: Multiple Oscap ARF reports can be deleted.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_reporting_emails_of_oscap_reports(self):
        """Email Reporting of oscap reports should be possible.

        :id: 003d4d28-f694-4e54-a149-247f58298ecc

        :expectedresults: Whether email reporting of oscap reports is possible.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
