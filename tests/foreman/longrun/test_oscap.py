"""Tests for the Oscap report upload feature

:Requirement: Oscap

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from fauxfactory import gen_string

from nailgun import entities
from robottelo.api.utils import wait_for_tasks
from robottelo.helpers import file_downloader, add_remote_execution_ssh_key, ProxyError
from robottelo.cli.arfreport import Arfreport
from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    make_hostgroup,
    make_scap_policy,
    make_tailoringfile
)
from robottelo.cli.ansible import Ansible
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.proxy import Proxy
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
    DEFAULT_LOC,
)
from robottelo.decorators import (
    skip_if_not_set,
    stubbed,
    tier4,
    upgrade
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


class OpenScapTestCase(CLITestCase):
    """Implements Product tests in CLI"""

    @classmethod
    @skip_if_not_set('oscap')
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
        cls.rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
        cls.rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        cls.config_env = cls.configure_puppet_test()

    @classmethod
    def fetch_scap_and_profile_id(cls, scap_name, scap_profile):
        """Extracts the scap ID and scap profile id

        :param scap_name: Scap title
        :param scap_profile: Scap profile you want to select

        :returns: scap_id and scap_profile_id
        """

        default_content = Scapcontent.info({'title': scap_name},
                                           output_format='json'
                                           )
        scap_id = default_content['id']
        scap_profile_ids = [
            profile['id']
            for profile in default_content['scap-content-profiles']
            if scap_profile in profile['title']
        ]
        return scap_id, scap_profile_ids

    @classmethod
    def configure_puppet_test(cls):
        """Sets up the whole provisioning environment needed for Puppet based
         end-to-end tests like OSCAP etc

         :returns: A dict of entities to help with provisioning
        """
        cls.rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
        cls.rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        sat6_hostname = settings.server.hostname
        proxy = Proxy.list({'search': sat6_hostname})[0]
        p_features = set(proxy.get('features').split(', '))
        if {'Puppet', 'Ansible', 'Openscap'}.issubset(p_features):
            cls.proxy_id = proxy.get('id')
        else:
            raise ProxyError('Some features like Puppet, DHCP, Openscap, Ansible are not present')
        ak_name_7 = gen_string('alpha')
        ak_name_6 = gen_string('alpha')
        repo_values = [
            {
                'repo': settings.sattools_repo['rhel6'],
                'akname': ak_name_6
            },
            {
                'repo': settings.sattools_repo['rhel7'],
                'akname': ak_name_7
            },
        ]
        # Create new organization and environment.
        org = entities.Organization(name=gen_string('alpha')).create()
        loc = entities.Location().search(query={'search': "{0}".format(DEFAULT_LOC)})[0].read()
        cls.puppet_env = entities.Environment().search(
            query={u'search': u'name=production'})[0].read()
        cls.puppet_env.location.append(loc)
        cls.puppet_env.organization.append(org)
        cls.puppet_env = cls.puppet_env.update(['location', 'organization'])
        smart_proxy = entities.SmartProxy().search(
            query={'search': 'name={0}'.format(sat6_hostname)})[0].read()
        smart_proxy.organization.append(entities.Organization(id=org.id))
        smart_proxy.location.append(entities.Location(id=loc.id))
        smart_proxy.update(['location', 'organization'])
        smart_proxy.import_puppetclasses(environment=cls.puppet_env.name)
        env = entities.LifecycleEnvironment(
            organization=org,
            name=gen_string('alpha')
        ).create()
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
            # Setup org for a custom repo for RHEL6 and RHEL7
            setup_org_for_a_custom_repo({
                'url': repo.get('repo'),
                'organization-id': org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': env.id,
                'activationkey-id': activation_key.id
            })

        for content in cls.rhel6_content, cls.rhel7_content:
            Scapcontent.update({
                'title': content,
                'organizations': org.name,
                'locations': DEFAULT_LOC
            })
        return {
            'org_name': org.name,
            'cv_name': content_view.name,
            'sat6_hostname': settings.server.hostname,
            'ak_name': {'rhel7': ak_name_7, 'rhel6': ak_name_6},
            'env_name': env.name,
        }

    @tier4
    @upgrade
    def test_positive_upload_to_satellite(self):
        """Perform end to end oscap test and upload reports via puppet

        :id: 17a0978d-64f9-44ad-8303-1f54ada08602

        :expectedresults: Oscap reports from rhel6 and rhel7 clients should be
            uploaded to satellite6 and be searchable.

        :CaseLevel: System

        :BZ: 1479413, 1722475
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
                'profile': OSCAP_PROFILE['security6']
            },
            {
                'content': self.rhel7_content,
                'hgrp': hgrp7_name,
                'policy': policy7_name,
                'profile': OSCAP_PROFILE['security7']
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

        # Creates host_group for both rhel6 and rhel7
        for host_group in [hgrp6_name, hgrp7_name]:
            make_hostgroup({
                'content-source': self.config_env['sat6_hostname'],
                'name': host_group,
                'puppet-environment-id': self.puppet_env.id,
                'puppet-ca-proxy': self.config_env['sat6_hostname'],
                'puppet-proxy': self.config_env['sat6_hostname'],
                'organizations': self.config_env['org_name'],
            })
        # Creates oscap_policy for both rhel6 and rhel7.
        for value in policy_values:
            scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
                value['content'],
                value['profile']
            )
            make_scap_policy({
                'scap-content-id': scap_id,
                'hostgroups': value['hgrp'],
                'deploy-by': 'puppet',
                'name': value['policy'],
                'period': OSCAP_PERIOD['weekly'].lower(),
                'scap-content-profile-id': scap_profile_id,
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'organizations': self.config_env['org_name'],
            })
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
                Host.update({
                    'name': vm.hostname.lower(),
                    'lifecycle-environment': self.config_env['env_name'],
                    'content-view': self.config_env['cv_name'],
                    'hostgroup': value['hgrp'],
                    'openscap-proxy-id': self.proxy_id,
                    'organization': self.config_env['org_name'],
                    'puppet-environment-id': self.puppet_env.id,
                })

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
                self.assertIsNotNone(Arfreport.list({'search': 'host={0}'.format(host)}))

    @upgrade
    @tier4
    def test_positive_push_updated_content(self):
        """Perform end to end oscap test, and push the updated scap content via puppet
         after first run.

        :id: 7eb75ca5-2ea1-434e-bb43-1223fa4d8e9f

        :expectedresults: Satellite should push updated content to Clients and
            satellite should get updated reports

        :CaseLevel: System

        :BZ: 1420439, 1722475
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
            'profile': OSCAP_PROFILE['security7']
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        Scapcontent.update({
            'title': content_update,
            'organizations': self.config_env['org_name']
        })
        # Creates host_group for rhel7
        make_hostgroup({
            'content-source-id': self.proxy_id,
            'name': hgrp7_name,
            'puppet-environment-id': self.puppet_env.id,
            'puppet-ca-proxy': self.config_env['sat6_hostname'],
            'puppet-proxy': self.config_env['sat6_hostname'],
            'organizations': self.config_env['org_name']
        })
        # Creates oscap_policy for rhel7.
        scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
            policy_values.get('content'),
            policy_values.get('profile')
        )
        make_scap_policy({
            'scap-content-id': scap_id,
            'deploy-by': 'puppet',
            'hostgroups': policy_values.get('hgrp'),
            'name': policy_values.get('policy'),
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'organizations': self.config_env['org_name']
        })
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
            Host.update({
                'name': vm.hostname.lower(),
                'lifecycle-environment': self.config_env['env_name'],
                'content-view': self.config_env['cv_name'],
                'hostgroup': vm_values.get('hgrp'),
                'openscap-proxy-id': self.proxy_id,
                'organization': self.config_env['org_name'],
                'puppet-environment-id': self.puppet_env.id,
            })
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
            arf_report = Arfreport.list(
                {
                    'search': 'host={0}'.format(vm.hostname.lower()),
                    'per-page': 1
                })
            self.assertIsNotNone(arf_report)
            scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
                OSCAP_DEFAULT_CONTENT['rhel_firefox'],
                OSCAP_PROFILE['firefox']
            )
            Scappolicy.update({
                'scap-content-id': scap_id,
                'deploy-by': 'puppet',
                'name': policy_values.get('policy'),
                'new-name': gen_string('alpha'),
                'period': OSCAP_PERIOD['weekly'].lower(),
                'scap-content-profile-id': scap_profile_id,
                'weekday': OSCAP_WEEKDAY['friday'].lower(),
                'organizations': self.config_env['org_name']
            })
            Arfreport.delete({'id': arf_report[0].get('id')})
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
            self.assertIsNotNone(
                Arfreport.list({'search': 'host={0}'.format(vm.hostname.lower())}))

    @upgrade
    @tier4
    def test_positive_oscap_run_with_tailoring_file_and_capsule(self):
        """ End-to-End Oscap run with tailoring files and default capsule via puppet

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

        :BZ: 1722475

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
            'profile': OSCAP_PROFILE['security7']
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        tailoring_file_name = gen_string('alpha')
        tailor_path = file_downloader(
            file_url=settings.oscap.tailoring_path,
            hostname=settings.server.hostname)[0]
        # Creates host_group for rhel7
        make_hostgroup({
            'content-source-id': self.proxy_id,
            'name': hgrp7_name,
            'puppet-environment-id': self.puppet_env.id,
            'puppet-ca-proxy': self.config_env['sat6_hostname'],
            'puppet-proxy': self.config_env['sat6_hostname'],
            'organizations': self.config_env['org_name']
        })

        tailor_result = make_tailoringfile({
            'name': tailoring_file_name,
            'scap-file': tailor_path,
            'organization': self.config_env['org_name']
        })
        result = TailoringFiles.info({'name': tailoring_file_name})
        self.assertEqual(result['name'], tailoring_file_name)
        # Creates oscap_policy for rhel7.
        scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
            policy_values.get('content'),
            policy_values.get('profile')
        )
        make_scap_policy({
            'scap-content-id': scap_id,
            'deploy-by': 'puppet',
            'hostgroups': policy_values.get('hgrp'),
            'name': policy_values.get('policy'),
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'tailoring-file-id': tailor_result['id'],
            'tailoring-file-profile-id': tailor_result['tailoring-file-profiles'][0]['id'],
            'organizations': self.config_env['org_name']
        })
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
            Host.update({
                'name': vm.hostname.lower(),
                'lifecycle-environment': self.config_env['env_name'],
                'content-view': self.config_env['cv_name'],
                'hostgroup': vm_values.get('hgrp'),
                'openscap-proxy-id': self.proxy_id,
                'organization': self.config_env['org_name'],
                'puppet-environment-id': self.puppet_env.id,
            })
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
            self.assertIsNotNone(
                Arfreport.list({'search': 'host={0}'.format(vm.hostname.lower())}))

    @upgrade
    @tier4
    def test_positive_oscap_run_with_tailoring_file_with_ansible(self):
        """ End-to-End Oscap run with tailoring files via ansible

        :id: c7ea56eb-6cf1-4e79-8d6a-fb872d1bb804

        :setup: scap content, scap policy, tailoring file, host group

        :steps:

            1. Create a valid scap content
            2. Upload a valid tailoring file
            3. Import Ansible role theforeman.foreman_scap_client
            4. Import Ansible Variables needed for the role
            5. Create a scap policy with anisble as deploy option
            6. Associate scap content with it's tailoring file
            7. Associate the policy with a hostgroup
            8. Provision a host using the hostgroup
            9. Configure REX and associate the Ansible role to created host
            10. Play roles for the host

        :expectedresults: REX job should be success and ARF report should be sent to satellite
                         reflecting the changes done via tailoring files

        :BZ: 1716307

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
            'profile': OSCAP_PROFILE['security7']
        }
        vm_values = {
            'distro': DISTRO_RHEL7,
            'hgrp': hgrp7_name,
            'rhel_repo': rhel7_repo,
        }
        tailoring_file_name = gen_string('alpha')
        tailor_path = file_downloader(
            file_url=settings.oscap.tailoring_path,
            hostname=settings.server.hostname)[0]
        # Creates host_group for rhel7
        make_hostgroup({
            'content-source-id': self.proxy_id,
            'name': hgrp7_name,
            'organizations': self.config_env['org_name']
        })

        tailor_result = make_tailoringfile({
            'name': tailoring_file_name,
            'scap-file': tailor_path,
            'organization': self.config_env['org_name']
        })
        result = TailoringFiles.info({'name': tailoring_file_name})
        self.assertEqual(result['name'], tailoring_file_name)
        # Creates oscap_policy for rhel7.
        scap_id, scap_profile_id = self.fetch_scap_and_profile_id(
            policy_values.get('content'),
            policy_values.get('profile')
        )
        Ansible.roles_import({'proxy-id': self.proxy_id})
        Ansible.variables_import({'proxy-id': self.proxy_id})
        role_id = Ansible.roles_list({'search': 'foreman_scap_client'})[0].get('id')
        make_scap_policy({
            'scap-content-id': scap_id,
            'hostgroups': policy_values.get('hgrp'),
            'deploy-by': 'ansible',
            'name': policy_values.get('policy'),
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'tailoring-file-id': tailor_result['id'],
            'tailoring-file-profile-id': tailor_result['tailoring-file-profiles'][0]['id'],
            'organizations': self.config_env['org_name']
        })
        distro_os = vm_values.get('distro')
        with VirtualMachine(distro=distro_os) as vm:
            host_name, _, host_domain = vm.hostname.partition('.')
            vm.install_katello_ca()
            vm.register_contenthost(
                self.config_env['org_name'],
                self.config_env['ak_name'].get(distro_os)
            )
            self.assertTrue(vm.subscribed)
            Host.set_parameter({
                'host': vm.hostname.lower(),
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            })
            vm.configure_rhel_repo(settings.rhel7_repo)
            add_remote_execution_ssh_key(vm.ip_addr)
            Host.update({
                'name': vm.hostname.lower(),
                'lifecycle-environment': self.config_env['env_name'],
                'content-view': self.config_env['cv_name'],
                'hostgroup': vm_values.get('hgrp'),
                'openscap-proxy-id': self.proxy_id,
                'organization': self.config_env['org_name'],
                'ansible-role-ids': role_id
            })
            job_id = Host.ansible_roles_play({'name': vm.hostname.lower()})[0].get('id')
            wait_for_tasks("resource_type = JobInvocation and resource_id = {0} and "
                           "action ~ \"hosts job\"".format(job_id))
            try:
                self.assertEqual(JobInvocation.info({'id': job_id})['success'], '1')
            except AssertionError:
                result = 'host output: {0}'.format(
                    ' '.join(JobInvocation.get_output({
                        'id': job_id,
                        'host': vm.hostname
                    })
                    )
                )
                raise AssertionError(result)
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
            self.assertIsNotNone(
                Arfreport.list({'search': 'host={0}'.format(vm.hostname.lower())}))

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

    @stubbed()
    @tier4
    def test_positive_reporting_emails_of_oscap_reports(self):
        """Email Reporting of oscap reports should be possible.

        :id: 003d4d28-f694-4e54-a149-247f58298ecc

        :expectedresults: Whether email reporting of oscap reports is possible.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
