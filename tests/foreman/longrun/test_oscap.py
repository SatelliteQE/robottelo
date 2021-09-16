"""Tests for the Oscap report upload feature

:Requirement: Oscap

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from broker.broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.ansible import Ansible
from robottelo.cli.arfreport import Arfreport
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_scap_policy
from robottelo.cli.factory import make_tailoringfile
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.proxy import Proxy
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.cli.scapcontent import Scapcontent
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.constants import OSCAP_DEFAULT_CONTENT
from robottelo.constants import OSCAP_PERIOD
from robottelo.constants import OSCAP_PROFILE
from robottelo.constants import OSCAP_TARGET_CORES
from robottelo.constants import OSCAP_TARGET_MEMORY
from robottelo.constants import OSCAP_WEEKDAY
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.helpers import file_downloader
from robottelo.helpers import ProxyError
from robottelo.hosts import ContentHost


puppet_classes = ['foreman_scap_client::params', 'foreman_scap_client']
rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
rhel8_content = OSCAP_DEFAULT_CONTENT['rhel8_content']
ak_name = {
    'rhel8': gen_string('alpha'),
    'rhel7': gen_string('alpha'),
    'rhel6': gen_string('alpha'),
}


def fetch_scap_and_profile_id(scap_name, scap_profile):
    """Extracts the scap ID and scap profile id

    :param scap_name: Scap title
    :param scap_profile: Scap profile you want to select

    :returns: scap_id and scap_profile_id
    """

    default_content = Scapcontent.info({'title': scap_name}, output_format='json')
    scap_id = default_content['id']
    scap_profile_ids = [
        profile['id']
        for profile in default_content['scap-content-profiles']
        if scap_profile in profile['title']
    ]
    return scap_id, scap_profile_ids


@pytest.fixture(scope='module')
def default_proxy(default_sat):
    """Returns default capsule/proxy id"""
    proxy = Proxy.list({'search': default_sat.hostname})[0]
    p_features = set(proxy.get('features').split(', '))
    if {'Puppet', 'Ansible', 'Openscap'}.issubset(p_features):
        proxy_id = proxy.get('id')
    else:
        raise ProxyError('Some features like Puppet, DHCP, Openscap, Ansible are not present')
    return proxy_id


@pytest.fixture(scope='module')
def puppet_env(module_org, import_puppet_classes):
    """Update puppet environment"""
    puppet_env = entities.Environment().search(query={'search': 'name=production'})[0].read()
    puppet_env.organization.append(module_org)
    puppet_env = puppet_env.update(['organization'])
    return puppet_env


@pytest.fixture(scope='module')
def lifecycle_env(module_org, puppet_env):
    """Create lifecycle environment"""
    lce_env = entities.LifecycleEnvironment(
        organization=module_org, name=gen_string('alpha')
    ).create()
    return lce_env


@pytest.fixture(scope='module')
def content_view(module_org):
    """Create content view"""
    return entities.ContentView(organization=module_org, name=gen_string('alpha')).create()


@pytest.fixture(scope='module', autouse=True)
def activation_key(module_org, lifecycle_env, content_view):
    """Create activation keys"""
    repo_values = [
        {'repo': settings.repos.sattools_repo.rhel8, 'akname': ak_name['rhel8']},
        {'repo': settings.repos.sattools_repo.rhel7, 'akname': ak_name['rhel7']},
        {'repo': settings.repos.sattools_repo.rhel6, 'akname': ak_name['rhel6']},
    ]

    for repo in repo_values:
        activation_key = entities.ActivationKey(
            name=repo.get('akname'), environment=lifecycle_env, organization=module_org
        ).create()
        # Setup org for a custom repo for RHEL6, RHEL7 and RHEL8.
        setup_org_for_a_custom_repo(
            {
                'url': repo.get('repo'),
                'organization-id': module_org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': lifecycle_env.id,
                'activationkey-id': activation_key.id,
            }
        )


@pytest.fixture(scope='module', autouse=True)
def update_scap_content(module_org):
    """Update default scap contents"""
    for content in rhel8_content, rhel7_content, rhel6_content:
        content = Scapcontent.info({'title': content}, output_format='json')
        organization_ids = [content_org['id'] for content_org in content.get('organizations', [])]
        organization_ids.append(module_org.id)
        Scapcontent.update({'title': content['title'], 'organization-ids': organization_ids})


@pytest.mark.tier4
@pytest.mark.upgrade
@pytest.mark.parametrize('distro', [DISTRO_RHEL6, DISTRO_RHEL7, DISTRO_RHEL8])
def test_positive_upload_to_satellite(
    module_org,
    default_proxy,
    content_view,
    lifecycle_env,
    puppet_env,
    distro,
    default_sat,
):
    """Perform end to end oscap test, and push the updated scap content via puppet
     after first run.

    :id: 11fef620-6ee8-4768-a398-db8cede1fc14

    :parametrized: yes

    :customerscenario: true

    :expectedresults: Oscap reports from rhel6, rhel7 and rhel8 clients should be
        uploaded to Satellite and be searchable. Satellite should push updated
        content to Clients and satellite should get updated reports.

    :CaseLevel: System

    :BZ: 1479413, 1722475, 1420439, 1722475
    """
    hgrp_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    if distro == 'rhel6':
        rhel_repo = settings.repos.rhel6_repo
        profile1 = OSCAP_PROFILE['dsrhel6']
        profile2 = OSCAP_PROFILE['pcidss6']
        profile3 = OSCAP_PROFILE['usgcb']
    elif distro == 'rhel7':
        rhel_repo = settings.repos.rhel7_repo
        profile1 = OSCAP_PROFILE['dsrhel7']
        profile2 = OSCAP_PROFILE['pcidss7']
        profile3 = OSCAP_PROFILE['ospp7']
    else:
        rhel_repo = settings.repos.rhel8_repo
        profile1 = OSCAP_PROFILE['dsrhel8']
        profile2 = OSCAP_PROFILE['pcidss8']
        profile3 = OSCAP_PROFILE['ospp8']
    content = OSCAP_DEFAULT_CONTENT[f'{distro}_content']
    # Creates host_group.
    make_hostgroup(
        {
            'content-source': default_sat.hostname,
            'name': hgrp_name,
            'puppet-environment-id': puppet_env.id,
            'puppet-ca-proxy': default_sat.hostname,
            'puppet-proxy': default_sat.hostname,
            'organizations': module_org.name,
            'puppet-classes': puppet_classes,
        }
    )
    # Creates oscap_policy.
    scap_id, scap_profile_id = fetch_scap_and_profile_id(content, profile1)
    make_scap_policy(
        {
            'scap-content-id': scap_id,
            'hostgroups': hgrp_name,
            'deploy-by': 'puppet',
            'name': policy_name,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'organizations': module_org.name,
        }
    )
    # Creates vm's and runs openscap scan and uploads report to satellite6.
    with VMBroker(
        nick=distro,
        host_classes={'host': ContentHost},
        target_cores=OSCAP_TARGET_CORES,
        target_memory=OSCAP_TARGET_MEMORY,
    ) as vm:
        host_name, _, host_domain = vm.hostname.partition('.')
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(module_org.name, ak_name[distro])
        assert vm.subscribed
        Host.update(
            {
                'name': vm.hostname.lower(),
                'lifecycle-environment': lifecycle_env.name,
                'content-view': content_view.name,
                'hostgroup': hgrp_name,
                'openscap-proxy-id': default_proxy,
                'organization': module_org.name,
                'puppet-environment-id': puppet_env.id,
            }
        )
        Host.set_parameter(
            {
                'host': vm.hostname.lower(),
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            }
        )
        SmartClassParameter.update(
            {
                'name': 'fetch_remote_resources',
                'override': 1,
                'parameter-type': 'boolean',
                'default-value': 'true',
                'puppet-class': 'foreman_scap_client',
            }
        )
        SmartClassParameter.add_matcher(
            {
                'smart-class-parameter': 'fetch_remote_resources',
                'match': f'fqdn={vm.hostname}',
                'value': 'true',
                'puppet-class': 'foreman_scap_client',
            }
        )

        vm.configure_puppet(rhel_repo, default_sat.hostname)
        result = vm.run('cat /etc/foreman_scap_client/config.yaml | grep profile')
        assert result.status == 0
        # Runs the actual oscap scan on the vm/clients and
        # uploads report to Internal Capsule.
        vm.execute_foreman_scap_client()
        # Assert whether oscap reports are uploaded to
        # Satellite6.
        arf_report = Arfreport.list({'search': f'host={vm.hostname.lower()}', 'per-page': 1})
        assert arf_report is not None
        for profile in [profile2, profile3]:
            scap_id, scap_profile_id = fetch_scap_and_profile_id(content, profile)
            Scappolicy.update(
                {
                    'scap-content-id': scap_id,
                    'deploy-by': 'puppet',
                    'name': policy_name,
                    'period': OSCAP_PERIOD['weekly'].lower(),
                    'scap-content-profile-id': scap_profile_id,
                    'weekday': OSCAP_WEEKDAY['friday'].lower(),
                    'organization': module_org.name,
                }
            )
            for _ in range(2):
                vm.run('puppet agent -t 2> /dev/null')
            updated_result = vm.run('cat /etc/foreman_scap_client/config.yaml | grep content_path')
            assert result != updated_result
            assert updated_result.status == 0
            # Runs the actual oscap scan on the vm/clients and
            # uploads report to Internal Capsule.
            vm.execute_foreman_scap_client()
            result = Arfreport.list({'search': f'host={vm.hostname.lower()}'})
            assert result is not None


@pytest.mark.upgrade
@pytest.mark.tier4
def test_positive_oscap_run_with_tailoring_file_and_capsule(
    module_org, default_proxy, content_view, lifecycle_env, puppet_env, default_sat
):
    """End-to-End Oscap run with tailoring files and default capsule via puppet

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
    hgrp_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    tailoring_file_name = gen_string('alpha')
    tailor_path = file_downloader(
        file_url=settings.oscap.tailoring_path, hostname=default_sat.hostname
    )[0]
    # Creates host_group.
    make_hostgroup(
        {
            'content-source': default_sat.hostname,
            'name': hgrp_name,
            'puppet-environment-id': puppet_env.id,
            'puppet-ca-proxy': default_sat.hostname,
            'puppet-proxy': default_sat.hostname,
            'organizations': module_org.name,
            'puppet-classes': puppet_classes,
        }
    )

    tailor_result = make_tailoringfile(
        {
            'name': tailoring_file_name,
            'scap-file': tailor_path,
            'organization': module_org.name,
        }
    )
    result = TailoringFiles.info({'name': tailoring_file_name})
    assert result['name'] == tailoring_file_name
    # Creates oscap_policy.
    scap_id, scap_profile_id = fetch_scap_and_profile_id(
        OSCAP_DEFAULT_CONTENT['rhel7_content'], OSCAP_PROFILE['security7']
    )
    make_scap_policy(
        {
            'scap-content-id': scap_id,
            'hostgroups': hgrp_name,
            'deploy-by': 'puppet',
            'name': policy_name,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'tailoring-file-id': tailor_result['id'],
            'tailoring-file-profile-id': tailor_result['tailoring-file-profiles'][0]['id'],
            'organizations': module_org.name,
        }
    )
    # Creates vm's and runs openscap scan and uploads report to satellite6.
    with VMBroker(
        nick=DISTRO_RHEL7,
        host_classes={'host': ContentHost},
        target_cores=OSCAP_TARGET_CORES,
        target_memory=OSCAP_TARGET_MEMORY,
    ) as vm:
        host_name, _, host_domain = vm.hostname.partition('.')
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(module_org.name, ak_name[DISTRO_RHEL7])
        assert vm.subscribed
        Host.update(
            {
                'name': vm.hostname.lower(),
                'lifecycle-environment': lifecycle_env.name,
                'content-view': content_view.name,
                'hostgroup': hgrp_name,
                'openscap-proxy-id': default_proxy,
                'organization': module_org.name,
                'puppet-environment-id': puppet_env.id,
            }
        )
        Host.set_parameter(
            {
                'host': vm.hostname.lower(),
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            }
        )
        vm.configure_puppet(settings.repos.rhel7_repo, default_sat.hostname)
        result = vm.run('cat /etc/foreman_scap_client/config.yaml | grep profile')
        assert result.status == 0
        # Runs the actual oscap scan on the vm/clients and
        # uploads report to Internal Capsule.
        vm.execute_foreman_scap_client()
        # Assert whether oscap reports are uploaded to
        # Satellite6.
        arf_report = Arfreport.list({'search': f'host={vm.hostname.lower()}', 'per-page': 1})
        assert arf_report is not None
        Arfreport.delete({'id': arf_report[0].get('id')})


@pytest.mark.upgrade
@pytest.mark.tier4
@pytest.mark.parametrize('distro', [DISTRO_RHEL7, DISTRO_RHEL8])
def test_positive_oscap_run_via_ansible(
    module_org, default_proxy, content_view, lifecycle_env, distro, default_sat
):
    """End-to-End Oscap run via ansible

    :id: c7ea56eb-6cf1-4e79-8d6a-fb872d1bb804

    :parametrized: yes

    :setup: scap content, scap policy, host group

    :steps:

        1. Create a valid scap content
        2. Import Ansible role theforeman.foreman_scap_client
        3. Import Ansible Variables needed for the role
        4. Create a scap policy with anisble as deploy option
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Configure REX and associate the Ansible role to created host
        8. Play roles for the host

    :expectedresults: REX job should be success and ARF report should be sent to satellite

    :BZ: 1716307

    :CaseImportance: Critical
    """
    if distro == 'rhel7':
        rhel_repo = settings.repos.rhel7_repo
        profile = OSCAP_PROFILE['security7']
    else:
        rhel_repo = settings.repos.rhel8_repo
        profile = OSCAP_PROFILE['ospp8']
    content = OSCAP_DEFAULT_CONTENT[f'{distro}_content']
    hgrp_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    # Creates host_group for rhel7
    make_hostgroup(
        {
            'content-source-id': default_proxy,
            'name': hgrp_name,
            'organizations': module_org.name,
        }
    )
    # Creates oscap_policy.
    scap_id, scap_profile_id = fetch_scap_and_profile_id(content, profile)
    Ansible.roles_import({'proxy-id': default_proxy})
    Ansible.variables_import({'proxy-id': default_proxy})
    role_id = Ansible.roles_list({'search': 'foreman_scap_client'})[0].get('id')
    make_scap_policy(
        {
            'scap-content-id': scap_id,
            'hostgroups': hgrp_name,
            'deploy-by': 'ansible',
            'name': policy_name,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'organizations': module_org.name,
        }
    )
    with VMBroker(
        nick=distro,
        host_classes={'host': ContentHost},
        target_cores=OSCAP_TARGET_CORES,
        target_memory=OSCAP_TARGET_MEMORY,
    ) as vm:
        host_name, _, host_domain = vm.hostname.partition('.')
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(module_org.name, ak_name[distro])
        assert vm.subscribed
        Host.set_parameter(
            {
                'host': vm.hostname.lower(),
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            }
        )
        vm.configure_rhel_repo(rhel_repo)
        add_remote_execution_ssh_key(vm.ip_addr)
        Host.update(
            {
                'name': vm.hostname.lower(),
                'lifecycle-environment': lifecycle_env.name,
                'content-view': content_view.name,
                'hostgroup': hgrp_name,
                'openscap-proxy-id': default_proxy,
                'organization': module_org.name,
                'ansible-role-ids': role_id,
            }
        )
        job_id = Host.ansible_roles_play({'name': vm.hostname.lower()})[0].get('id')
        wait_for_tasks(
            f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
        )
        try:
            result = JobInvocation.info({'id': job_id})['success']
            assert result == '1'
        except AssertionError:
            output = ' '.join(JobInvocation.get_output({'id': job_id, 'host': vm.hostname}))
            result = f'host output: {output}'
            raise AssertionError(result)
        result = vm.run('cat /etc/foreman_scap_client/config.yaml | grep profile')
        assert result.status == 0
        # Runs the actual oscap scan on the vm/clients and
        # uploads report to Internal Capsule.
        vm.execute_foreman_scap_client()
        # Assert whether oscap reports are uploaded to
        # Satellite6.
        result = Arfreport.list({'search': f'host={vm.hostname.lower()}'})
        assert result is not None


@pytest.mark.tier4
def test_positive_oscap_run_via_ansible_bz_1814988(
    module_org, default_proxy, content_view, lifecycle_env, default_sat
):
    """End-to-End Oscap run via ansible

    :id: 375f8f08-9299-4d16-91f9-9426eeecb9c5

    :parametrized: yes

    :customerscenario: true

    :setup: scap content, scap policy, host group

    :steps:

        1. Create a valid scap content
        2. Import Ansible role theforeman.foreman_scap_client
        3. Import Ansible Variables needed for the role
        4. Create a scap policy with anisble as deploy option
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Harden the host by remediating it with DISA STIG security policy
        8. Configure REX and associate the Ansible role to created host
        9. Play roles for the host

    :expectedresults: REX job should be success and ARF report should be sent to satellite

    :BZ: 1814988

    :CaseImportance: Critical
    """
    hgrp_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    # Creates host_group for rhel7
    make_hostgroup(
        {
            'content-source-id': default_proxy,
            'name': hgrp_name,
            'organizations': module_org.name,
        }
    )
    # Creates oscap_policy.
    scap_id, scap_profile_id = fetch_scap_and_profile_id(
        OSCAP_DEFAULT_CONTENT['rhel7_content'], OSCAP_PROFILE['dsrhel7']
    )
    Ansible.roles_import({'proxy-id': default_proxy})
    Ansible.variables_import({'proxy-id': default_proxy})
    role_id = Ansible.roles_list({'search': 'foreman_scap_client'})[0].get('id')
    make_scap_policy(
        {
            'scap-content-id': scap_id,
            'hostgroups': hgrp_name,
            'deploy-by': 'ansible',
            'name': policy_name,
            'period': OSCAP_PERIOD['weekly'].lower(),
            'scap-content-profile-id': scap_profile_id,
            'weekday': OSCAP_WEEKDAY['friday'].lower(),
            'organizations': module_org.name,
        }
    )
    with VMBroker(
        nick=DISTRO_RHEL7,
        host_classes={'host': ContentHost},
        target_cores=OSCAP_TARGET_CORES,
        target_memory=OSCAP_TARGET_MEMORY,
    ) as vm:
        host_name, _, host_domain = vm.hostname.partition('.')
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(module_org.name, ak_name[DISTRO_RHEL7])
        assert vm.subscribed
        Host.set_parameter(
            {
                'host': vm.hostname.lower(),
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            }
        )
        vm.configure_rhel_repo(settings.repos.rhel7_repo)
        # Harden the rhel7 client with DISA STIG security policy
        vm.run('yum install -y scap-security-guide')
        vm.run(
            'oscap xccdf eval --remediate --profile xccdf_org.ssgproject.content_profile_stig '
            '--fetch-remote-resources --results-arf results.xml '
            '/usr/share/xml/scap/ssg/content/ssg-rhel7-ds.xml',
        )
        add_remote_execution_ssh_key(vm.ip_addr)
        Host.update(
            {
                'name': vm.hostname.lower(),
                'lifecycle-environment': lifecycle_env.name,
                'content-view': content_view.name,
                'hostgroup': hgrp_name,
                'openscap-proxy-id': default_proxy,
                'organization': module_org.name,
                'ansible-role-ids': role_id,
            }
        )
        job_id = Host.ansible_roles_play({'name': vm.hostname.lower()})[0].get('id')
        wait_for_tasks(
            f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
        )
        try:
            result = JobInvocation.info({'id': job_id})['success']
            assert result == '1'
        except AssertionError:
            output = ' '.join(JobInvocation.get_output({'id': job_id, 'host': vm.hostname}))
            result = f'host output: {output}'
            raise AssertionError(result)
        result = vm.run('cat /etc/foreman_scap_client/config.yaml | grep profile')
        assert result.status == 0
        # Runs the actual oscap scan on the vm/clients and
        # uploads report to Internal Capsule.
        vm.execute_foreman_scap_client()
        # Assert whether oscap reports are uploaded to
        # Satellite6.
        result = Arfreport.list({'search': f'host={vm.hostname.lower()}'})
        assert result is not None


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_has_arf_report_summary_page():
    """OSCAP ARF Report now has summary page

    :id: 25be7898-50c5-4825-adc7-978c7b4e3488

    :Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Oscap ARF reports should have summary page.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_view_full_report_button():
    """'View full Report' button should exist for OSCAP Reports.

    :id: 5a41916d-66db-4d2f-8261-b83f833189b9

    :Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Should have 'view full report' button to view the
        actual HTML report.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_download_xml_button():
    """'Download xml' button should exist for OSCAP Reports
    to be downloaded in xml format.

    :id: 07a5f495-a702-4ca4-b5a4-579a133f9181

    :Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Should have 'Download xml in bzip' button to download
        the xml report.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_select_oscap_proxy():
    """Oscap-Proxy select box should exist while filling hosts
    and host-groups form.

    :id: d56576c8-6fab-4af6-91c1-6a56d9cca94b

    :Steps: Choose the Oscap Proxy/capsule appropriately for the host or
        host-groups.

    :expectedresults: Should have an Oscap-Proxy select box while filling
        hosts and host-groups form.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_delete_multiple_arf_reports():
    """Multiple arf reports deletion should be possible.

    :id: c1a8ce02-f42f-4c48-893d-8f31432b5520

    :Steps:
        1. Run Oscap scans are run for multiple Hosts.
        2. Make sure the oscap reports with it's corresponding hostnames
           are visible in the UI.
        3. Now select multiple reports from the checkbox and delete the
           reports.

    :expectedresults: Multiple Oscap ARF reports can be deleted.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier4
def test_positive_reporting_emails_of_oscap_reports():
    """Email Reporting of oscap reports should be possible.

    :id: 003d4d28-f694-4e54-a149-247f58298ecc

    :expectedresults: Whether email reporting of oscap reports is possible.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
