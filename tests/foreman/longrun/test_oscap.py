"""Tests for the Oscap report upload feature

:Requirement: Oscap

:CaseAutomation: Automated

:CaseComponent: SCAPPlugin

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from robottelo.exceptions import ProxyError
from robottelo.hosts import ContentHostError
from robottelo.logging import logger

ak_name = {
    'rhel10': f'ak_{gen_string("alpha")}_rhel10',
    'rhel9': f'ak_{gen_string("alpha")}_rhel9',
    'rhel8': f'ak_{gen_string("alpha")}_rhel8',
    'rhel7': f'ak_{gen_string("alpha")}_rhel7',
}
cv_name = {
    'rhel10': f'cv_{gen_string("alpha")}_rhel10',
    'rhel9': f'cv_{gen_string("alpha")}_rhel9',
    'rhel8': f'cv_{gen_string("alpha")}_rhel8',
    'rhel7': f'cv_{gen_string("alpha")}_rhel7',
}
profiles = {
    'rhel10': OSCAP_PROFILE['cbrhel10'],
    'rhel9': OSCAP_PROFILE['ospp8+'],
    'rhel8': OSCAP_PROFILE['ospp8+'],
    'rhel7': OSCAP_PROFILE['security7'],
}
rhel_repos = {
    'rhel10': settings.repos.rhel10_os,
    'rhel9': settings.repos.rhel9_os,
    'rhel8': settings.repos.rhel8_os,
    'rhel7': settings.repos.rhel7_os,
}


def fetch_scap_and_profile_id(sat, scap_name, scap_profile):
    """Extracts the scap ID and scap profile id

    :param scap_name: Scap title
    :param scap_profile: Scap profile you want to select

    :return: scap_id and scap_profile_id
    """
    default_content = sat.cli.Scapcontent.info({'title': scap_name}, output_format='json')
    scap_id = default_content['id']
    scap_profile_ids = [
        profile['id']
        for profile in default_content['scap-content-profiles']
        if scap_profile in profile['title']
    ]
    return scap_id, scap_profile_ids


@pytest.fixture(scope='module')
def default_proxy(module_target_sat):
    """Returns default capsule/proxy id"""
    proxy = module_target_sat.cli.Proxy.list({'search': module_target_sat.hostname})[0]
    p_features = set(proxy.get('features').split(', '))
    if {'Ansible', 'Openscap'}.issubset(p_features):
        proxy_id = proxy.get('id')
    else:
        raise ProxyError('Some features like DHCP, Openscap, Ansible are not present')
    return proxy_id


@pytest.fixture(scope='module')
def lifecycle_env(module_target_sat, module_org):
    """Create lifecycle environment"""
    return module_target_sat.api.LifecycleEnvironment(
        organization=module_org, name=gen_string('alpha')
    ).create()


@pytest.fixture(scope='module')
def content_view(module_target_sat, module_org):
    """Create content view"""
    return module_target_sat.api.ContentView(
        organization=module_org, name=gen_string('alpha')
    ).create()


@pytest.fixture(scope='module', autouse=True)
def activation_key(module_target_sat, module_org, lifecycle_env):
    """Create activation keys"""
    repo_values = [
        {
            'repo': getattr(settings.repos.satclient_repo, rhel),
            'akname': ak_name[rhel],
            'cvname': cv_name[rhel],
        }
        for rhel in ('rhel10', 'rhel9', 'rhel8', 'rhel7')
    ]

    for repo in repo_values:
        content_view = module_target_sat.api.ContentView(
            organization=module_org, name=repo.get('cvname')
        ).create()
        content_view.publish()
        content_view = content_view.read()
        assert len(content_view.version) == 1, "CV not published"
        version = content_view.version[0].read()
        version.promote(data={'environment_ids': lifecycle_env.id, 'force': True})
        activation_key = module_target_sat.api.ActivationKey(
            name=repo.get('akname'),
            environment=lifecycle_env,
            content_view=content_view,
            organization=module_org,
        ).create()
        # Setup org for a custom repo for RHEL6, RHEL7 and RHEL8.
        module_target_sat.cli_factory.setup_org_for_a_custom_repo(
            {
                'url': repo.get('repo'),
                'organization-id': module_org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': lifecycle_env.id,
                'activationkey-id': activation_key.id,
            }
        )


def update_scap_content(org, sat, content_title):
    """Update default scap contents"""
    logger.debug(f'Updating scap content "{content_title}"')
    content = sat.cli.Scapcontent.info({'title': content_title}, output_format='json')
    organization_ids = [str(content_org['id']) for content_org in content.get('organizations', [])]
    organization_ids.append(str(org.id))
    # any duplication causes validation error during update
    organization_ids_set = set(organization_ids)
    logger.debug(f'Assigning orgs {organization_ids} to scap content "{content_title}"')
    sat.cli.Scapcontent.update(
        {'title': content['title'], 'organization-ids': list(organization_ids_set)}
    )


def upload_scap_content_for_host(target_sat, contenthost, org):
    """Upload scap contents from client to Satellite.
    Default scap content present on Satellite depends on the underlying rhel version (SAT-19336)"""

    result = contenthost.execute('yum install -y scap-security-guide')
    if result.status != 0:
        raise ContentHostError('Failed to install scap-security-guide')
    content_dir = '/usr/share/xml/scap/ssg/content/'
    result = target_sat.execute(
        f'''sshpass -p "{settings.server.ssh_password}" scp -o StrictHostKeyChecking=no root@{contenthost.hostname}:{content_dir}* {content_dir}'''
    )
    assert result.status == 0, f'failed to copy content data from {contenthost.hostname}'
    target_sat.cli.Scapcontent.bulk_upload(
        {'type': 'directory', 'directory': content_dir, 'organization-id': org.id}
    )


def get_existing_content(target_sat):
    """List existing scap content"""
    existing_content = target_sat.cli.Scapcontent.list()
    logger.debug(f'Listing existing content on Satellite: {existing_content}')
    return [content['title'] for content in existing_content]


def find_content_to_update(target_sat, module_org, distro, contenthost):
    """find out what content to update based on existing content"""
    selected_content = OSCAP_DEFAULT_CONTENT[f'{distro}_content']
    existing_content_names = get_existing_content(target_sat)
    # the content name depends on upload style (default vs file upload)
    if (selected_content not in existing_content_names) and (
        f'{distro} content' not in existing_content_names
    ):
        upload_scap_content_for_host(target_sat, contenthost, module_org)

    # re-list after content upload
    existing_content_names = get_existing_content(target_sat)
    # find out content name for client version
    assert (selected_content in existing_content_names) or (
        f'{distro} content' in existing_content_names
    ), f'scap content not found for {distro}, existing content: {existing_content_names}'
    return selected_content if (selected_content in existing_content_names) else f'{distro} content'


def prepare_scap_client_and_prerequisites(
    target_sat, contenthost, module_org, default_proxy, lifecycle_env, profile=None
):
    """prepare scap client and create scap prerequisites on satellite, we are sourcing
    content files from the content hosts, hence this function can not be a fixture
    """
    os_version = contenthost.os_version.major
    distro = f'rhel{os_version}'

    target_sat.cli.Ansible.roles_import({'proxy-id': default_proxy})
    target_sat.cli.Ansible.variables_import({'proxy-id': default_proxy})
    role_id = target_sat.cli.Ansible.roles_list({'search': 'foreman_scap_client'})[0].get('id')

    # Create a hostgroup
    hgrp_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    hostgroup = target_sat.cli_factory.hostgroup(
        {
            'content-source-id': default_proxy,
            'name': hgrp_name,
            'organization': module_org.name,
            'lifecycle-environment': lifecycle_env.name,
            'content-view': cv_name[distro],
            'ansible-role-ids': role_id,
            'openscap-proxy-id': default_proxy,
        }
    )

    # Adding IPv6 proxy for IPv6 communication
    contenthost.enable_ipv6_dnf_and_rhsm_proxy()
    contenthost.enable_ipv6_system_proxy()

    # Register a host
    result = contenthost.register(
        module_org,
        None,
        ak_name[distro],
        target_sat,
        ignore_subman_errors=True,
        force=True,
        insecure=True,
        hostgroup=hostgroup,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    rhel_repo = rhel_repos[distro]
    if profile is None:
        profile = profiles[distro]
    if distro == 'rhel7':
        contenthost.create_custom_repos(**{distro: rhel_repo})
    else:
        contenthost.create_custom_repos(**rhel_repo)

    # Create SCAP content
    content = find_content_to_update(target_sat, module_org, distro, contenthost)
    update_scap_content(module_org, target_sat, content)

    # Create oscap_policy.
    scap_id, scap_profile_id = fetch_scap_and_profile_id(target_sat, content, profile)
    target_sat.cli_factory.make_scap_policy(
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


@pytest.fixture
def setup_pruned_content(target_sat, rex_contenthost, module_org):
    content_name = 'Red Hat rhel9 default content'
    old_package = 'scap-security-guide-satellite-4.3.4-1.el9sat.noarch.rpm'
    new_package = 'scap-security-guide-satellite-4.3.5-1.el9sat.noarch.rpm'
    # delete all policies because they may be using the scap content we want to delete
    policies = target_sat.cli.Scappolicy.list()
    for policy_id in [policy['id'] for policy in policies]:
        target_sat.cli.Scappolicy.delete({'id': policy_id})
    tmp_content_name = gen_string("alpha")
    # just doing
    # target_sat.cli.Scapcontent.delete({'title': content_name})
    # would break other tests that need full version of this content
    target_sat.cli.Scapcontent.update({'title': content_name, 'new-title': tmp_content_name})
    target_sat.put(f'tests/foreman/data/{old_package}', '/root/')
    target_sat.put(f'tests/foreman/data/{new_package}', '/root/')
    target_sat.execute(f'yum install -y {old_package}')
    target_sat.cli.Scapcontent.bulk_upload({'type': 'default'})
    yield new_package
    # delete all policies because they may be using the scap content we want to delete
    policies = target_sat.cli.Scappolicy.list()
    for policy_id in [policy['id'] for policy in policies]:
        target_sat.cli.Scappolicy.delete({'id': policy_id})
    target_sat.cli.Scapcontent.delete({'title': content_name})
    target_sat.cli.Scapcontent.update({'title': tmp_content_name, 'new-title': content_name})


def apply_policy_run_scan_get_arf(target_sat, contenthost):
    # Apply policy
    job_id = target_sat.cli.Host.ansible_roles_play({'name': contenthost.hostname.lower()})[0].get(
        'id'
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
    )
    try:
        result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
        assert result == '1'

    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output({'id': job_id, 'host': contenthost.hostname})
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err
    result = contenthost.execute_foreman_scap_client()
    arf_id = target_sat.cli.Arfreport.list({'search': f'host={contenthost.hostname.lower()}'})[0][
        'id'
    ]
    result = target_sat.cli.Arfreport.downloadhtml({'id': arf_id, 'path': '/tmp'})
    arf_report_path = result['message'].split(' ')[-1]
    return target_sat.execute(f'cat {arf_report_path}').stdout


@pytest.mark.rhel_ver_match('9')
def test_positive_oscap_update_default_content(
    module_org,
    default_proxy,
    lifecycle_env,
    target_sat,
    rex_contenthost,
    setup_pruned_content,
):
    """Update default scap package

    :id: a89634fb-152e-4fb5-8e69-7222a5a8b49f

    :setup:

        0. have a contenthost
        1. remove default rhel9 scap content
        2. yum install the pruned rhel9 scap content from a newer package version
        3. upload that content using hammer
        4. set up a policy from that content
        5. assign a policy to the host
        6. assign the scap client role to the host
        7. setup the host for scap scans by running ansible roles

    :steps:

        0. run a scap scan on the host, check the arf report contains one scan result
        1. yum install the pruned rhel9 scap content with some change in test name, from an even newer package version
        2. run ansible roles on the host again so it reflects changes
        3. run a scap scan on the host

    :expectedresults: the arf report contains the changed test name in results

    :Verifies: SAT-27369

    :customerscenario: true

    :CaseImportance: High
    """
    contenthost = rex_contenthost
    prepare_scap_client_and_prerequisites(
        target_sat,
        contenthost,
        module_org,
        default_proxy,
        lifecycle_env,
        profile='ANSSI-BP-028 (enhanced)',
    )

    arf_report = apply_policy_run_scan_get_arf(target_sat, contenthost)
    assert 'Set Password Minimum Length in login.defs' in arf_report
    assert 'FISH' not in arf_report

    # install the newest package version that contains word "FISH"
    target_sat.execute(f'yum install -y {setup_pruned_content}')
    target_sat.cli.Scapcontent.bulk_upload({'type': 'default'})

    arf_report = apply_policy_run_scan_get_arf(target_sat, contenthost)
    assert 'FISH' in arf_report


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.rhel_ver_match('[^6].*')
@pytest.mark.client_release
@pytest.mark.pit_server
@pytest.mark.pit_client
def test_positive_oscap_run_via_ansible(
    module_org,
    default_proxy,
    lifecycle_env,
    target_sat,
    rex_contenthost,
):
    """End-to-End Oscap run via ansible

    :id: c7ea56eb-6cf1-4e79-8d6a-fb872d1bb804

    :parametrized: yes

    :setup: scap content, scap policy, host group

    :steps:

        1. Create a valid scap content
        2. Import Ansible role theforeman.foreman_scap_client
        3. Import Ansible Variables needed for the role
        4. Create a scap policy with ansible as deploy option
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Configure REX and associate the Ansible role to created host
        8. Play roles for the host

    :expectedresults: REX job should be success and ARF report should be sent to satellite

    :BZ: 1716307, 1992229

    :Verifies: SAT-19389, SAT-24988, SAT-19491, SAT-28826

    :customerscenario: true

    :CaseImportance: Critical
    """
    contenthost = rex_contenthost
    prepare_scap_client_and_prerequisites(
        target_sat, contenthost, module_org, default_proxy, lifecycle_env
    )

    # check smart_proxy_openscap setup (SAT-28826)
    cronline = (
        '*/30 * * * * foreman-proxy smart-proxy-openscap-send >> /var/log/foreman-proxy/cron.log'
    )
    result = target_sat.execute('cat /etc/cron.d/rubygem-smart_proxy_openscap')
    assert cronline in result.stdout, 'smart_proxy_openscap cron not found'
    result = target_sat.execute('sudo -u foreman-proxy smart-proxy-openscap-send')
    assert result.status == 0

    # Apply policy
    job_id = target_sat.cli.Host.ansible_roles_play({'name': contenthost.hostname.lower()})[0].get(
        'id'
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
    )
    try:
        result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
        assert result == '1'
    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output({'id': job_id, 'host': contenthost.hostname})
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err
    result = contenthost.run('grep profile /etc/foreman_scap_client/config.yaml')
    assert result.status == 0
    contenthost.execute_foreman_scap_client()
    result = target_sat.cli.Arfreport.list({'search': f'host={contenthost.hostname.lower()}'})
    assert result is not None


@pytest.mark.e2e
@pytest.mark.rhel_ver_list([8])
@pytest.mark.client_release
def test_positive_oscap_remediation(
    module_org, default_proxy, content_view, lifecycle_env, target_sat, rex_contenthost
):
    """Run an OSCAP scan and remediate through WebUI

    :id: 55b919ef-432f-4186-b22a-01bb8ce39b3f

    :Verifies: SAT-23240

    :setup: scap content, scap policy, host group associated with the policy

    :steps:

        1. Create a valid scap content
        2. Import Ansible role theforeman.foreman_scap_client
        3. Import Ansible Variables needed for the role
        4. Create a scap policy with ansible as deploy option
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Configure REX and associate the Ansible role to created host
        8. Play roles for the host
        9. In WebUI, take a look at the ARF report and remediate one of the failures

    :expectedresults: REX job should be success and ARF report should be sent to satellite

    :customerscenario: true

    :CaseImportance: High
    """

    contenthost = rex_contenthost
    prepare_scap_client_and_prerequisites(
        target_sat, contenthost, module_org, default_proxy, lifecycle_env
    )

    # Apply policy
    job_id = target_sat.cli.Host.ansible_roles_play({'name': contenthost.hostname.lower()})[0].get(
        'id'
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
    )
    result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
    try:
        result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
        assert result == '1'
    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output({'id': job_id, 'host': contenthost.hostname})
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err

    # Run the actual oscap scan on the clients and
    # upload report to Internal Capsule.
    contenthost.execute_foreman_scap_client()
    arf_id = target_sat.cli.Arfreport.list({'search': f'host={contenthost.hostname.lower()}'})[0][
        'id'
    ]

    # Remediate
    with target_sat.ui_session() as session:
        assert contenthost.execute('rpm -q aide').status != 0, (
            'This test expects package "aide" NOT to be installed but it is. If this fails, it\'s probably a matter of wrong assumption of this test, not a product bug.'
        )
        title = 'xccdf_org.ssgproject.content_rule_package_aide_installed'
        session.organization.select(module_org.name)
        results = session.oscapreport.details(f'id={arf_id}', widget_names=['table'], limit=10)[
            'table'
        ]
        results_failed = [result for result in results if result['Result'] == 'fail']
        if title not in [result['Resource'] for result in results_failed]:
            results = session.oscapreport.details(f'id={arf_id}', widget_names=['table'])['table']
            results_failed = [result for result in results if result['Result'] == 'fail']
        assert title in [result['Resource'] for result in results_failed], (
            'This test expects the report to contain failure of "aide" package presence check. If this fails, it\'s probably a matter of wrong assumption of this test, not a product bug.'
        )
        session.oscapreport.remediate(f'id={arf_id}', title)
    wait_for(
        lambda: contenthost.execute("rpm -q aide").status == 0,
        timeout=300,
        delay=10,
    )
    assert contenthost.execute("rpm -q aide").status == 0


@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_oscap_run_via_ansible_bz_1814988(
    module_org, default_proxy, lifecycle_env, target_sat, rex_contenthost
):
    """End-to-End Oscap run with DISA remediation

    :id: 375f8f08-9299-4d16-91f9-9426eeecb9c5

    :parametrized: yes

    :customerscenario: true

    :setup: scap content, scap policy, host group

    :steps:

        1. Import Ansible role theforeman.foreman_scap_client
        2. Import Ansible Variables needed for the role
        3. Create a hostgroup
        4. Provision a host using the hostgroup
        5. Harden the host by remediating it with DISA STIG security policy
        6. Create a valid scap content
        7. Create a scap policy associated with the hostgroup and ansible as deploy option
        8. Play roles for the host

    :expectedresults: REX job should be success and ARF report should be sent to satellite

    :BlockedBy: SAT-19505

    :Verifies: SAT-19505
    """
    contenthost = rex_contenthost
    os_version = contenthost.os_version.major
    distro = f'rhel{os_version}'
    prepare_scap_client_and_prerequisites(
        target_sat, contenthost, module_org, default_proxy, lifecycle_env
    )

    # Harden the client with DISA STIG security policy
    contenthost.run('yum install -y scap-security-guide')
    contenthost.run(
        'oscap xccdf eval --remediate --profile xccdf_org.ssgproject.content_profile_stig '
        '--fetch-remote-resources --results-arf results.xml '
        f'/usr/share/xml/scap/ssg/content/ssg-{distro}-ds.xml',
    )

    # disable gpgcheck enabled by the above security policy
    contenthost.run(
        "sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.repos.d/foreman_registration1.repo "
    )
    # Apply policy
    job_id = target_sat.cli.Host.ansible_roles_play({'name': contenthost.hostname.lower()})[0].get(
        'id'
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
    )
    try:
        result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
        assert result == '1'
    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output({'id': job_id, 'host': contenthost.hostname})
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err
    result = contenthost.run('grep profile /etc/foreman_scap_client/config.yaml')
    assert result.status == 0
    contenthost.execute_foreman_scap_client()
    result = target_sat.cli.Arfreport.list({'search': f'host={contenthost.hostname.lower()}'})
    assert result is not None


@pytest.mark.stubbed
def test_positive_has_arf_report_summary_page():
    """OSCAP ARF Report now has summary page

    :id: 25be7898-50c5-4825-adc7-978c7b4e3488

    :steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Oscap ARF reports should have summary page.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_view_full_report_button():
    """'View full Report' button should exist for OSCAP Reports.

    :id: 5a41916d-66db-4d2f-8261-b83f833189b9

    :steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Should have 'view full report' button to view the
        actual HTML report.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_download_xml_button():
    """'Download xml' button should exist for OSCAP Reports
    to be downloaded in xml format.

    :id: 07a5f495-a702-4ca4-b5a4-579a133f9181

    :steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

    :expectedresults: Should have 'Download xml in bzip' button to download
        the xml report.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_select_oscap_proxy():
    """Oscap-Proxy select box should exist while filling hosts
    and host-groups form.

    :id: d56576c8-6fab-4af6-91c1-6a56d9cca94b

    :steps: Choose the Oscap Proxy/capsule appropriately for the host or
        host-groups.

    :expectedresults: Should have an Oscap-Proxy select box while filling
        hosts and host-groups form.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_delete_multiple_arf_reports():
    """Multiple arf reports deletion should be possible.

    :id: c1a8ce02-f42f-4c48-893d-8f31432b5520

    :steps:
        1. Run Oscap scans are run for multiple Hosts.
        2. Make sure the oscap reports with it's corresponding hostnames
           are visible in the UI.
        3. Now select multiple reports from the checkbox and delete the
           reports.

    :expectedresults: Multiple Oscap ARF reports can be deleted.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_reporting_emails_of_oscap_reports():
    """Email Reporting of oscap reports should be possible.

    :id: 003d4d28-f694-4e54-a149-247f58298ecc

    :expectedresults: Whether email reporting of oscap reports is possible.

    :CaseAutomation: NotAutomated
    """
