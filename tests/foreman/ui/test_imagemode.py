"""UI tests for Image Mode Hosts

:Requirement: ImageMode

:CaseAutomation: Automated

:CaseComponent: ImageMode

:Team: Artemis

:CaseImportance: High
"""

import json
import time

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DUMMY_BOOTC_FACTS,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from tests.foreman.longrun.test_oscap import (
    fetch_scap_and_profile_id,
    find_content_to_update,
    update_scap_content,
)

# Settings for oscap test


def test_bootc_booted_container_images(
    target_sat, dummy_bootc_host, function_ak_with_cv, function_org
):
    """Create a bootc host with a dummy facts file, and read its information via the Booted Container Images UI

    :id: c15f02a2-05e0-447a-bbcc-aace08d40d1a

    :expectedresults: Booted Container Images contains the correct information for a given booted image

    :Verifies:SAT-27163
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert (
        dummy_bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status
        == 0
    )
    assert dummy_bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        booted_container_image_info = session.bootc.read(bootc_dummy_info['bootc.booted.image'])
        assert (
            booted_container_image_info[0]['Image name'] == bootc_dummy_info['bootc.booted.image']
        )
        assert booted_container_image_info[0]['Image digests'] == '1'
        assert booted_container_image_info[0]['Hosts'] == '1'
        assert (
            booted_container_image_info[1]['Image digest']
            == bootc_dummy_info['bootc.booted.digest']
        )
        assert booted_container_image_info[1]['Hosts'] == '1'


def test_bootc_host_details(target_sat, dummy_bootc_host, function_ak_with_cv, function_org):
    """Create a bootc host, and read it's information via the Host Details UI

    :id: 842356e9-8798-421d-aca6-0a1774c3f22b

    :expectedresults: Host Details UI contains the proper information for a bootc host

    :Verifies:SAT-27171
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert (
        dummy_bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status
        == 0
    )
    assert dummy_bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        values = session.host_new.get_details(
            dummy_bootc_host.hostname, widget_names='details.bootc'
        )
        assert (
            values['details']['bootc']['details']['running_image']
            == bootc_dummy_info['bootc.booted.image']
        )
        assert (
            values['details']['bootc']['details']['running_image_digest']
            == bootc_dummy_info['bootc.booted.digest']
        )
        assert (
            values['details']['bootc']['details']['rollback_image']
            == bootc_dummy_info['bootc.rollback.image']
        )
        assert (
            values['details']['bootc']['details']['rollback_image_digest']
            == bootc_dummy_info['bootc.rollback.digest']
        )


def test_bootc_rex_job(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Run all bootc rex job (switch, upgrade, rollback, status) through Host Details UI

    :id: ef92a5f7-8cc7-4849-822c-90ea68b10554

    :expectedresults: Host Details UI links to the proper template, which runs successfully for all templates

    :Verifies:SAT-27154, SAT-27158
    """
    BOOTC_SWITCH_TARGET = "images.paas.redhat.com/bootc/rhel-bootc:latest-10.0"
    BOOTC_BASE_IMAGE = "localhost/tpl-bootc-rhel-10.0:latest"
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        # bootc status
        session.host_new.run_bootc_job(bootc_host.hostname, 'status')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc status on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert f'image: {BOOTC_BASE_IMAGE}' in task_status['humanized']['output']
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        # bootc switch
        session.host_new.run_bootc_job(
            bootc_host.hostname, 'switch', job_options=BOOTC_SWITCH_TARGET
        )
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc switch on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        assert f'Queued for next boot: {BOOTC_SWITCH_TARGET}' in task_status['humanized']['output']
        # bootc upgrade
        session.host_new.run_bootc_job(bootc_host.hostname, 'upgrade')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc upgrade on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        assert f'No changes in {BOOTC_SWITCH_TARGET}' in task_status['humanized']['output']
        # reboot the host, to ensure there is a rollback image
        bootc_host.execute('reboot')
        bootc_host.wait_for_connection()
        # bootc rollback
        session.host_new.run_bootc_job(bootc_host.hostname, 'rollback')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc rollback on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Next boot: rollback deployment' in task_status['humanized']['output']
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        # Check that the display in host details matches the task output
        values = session.host_new.get_details(bootc_host.hostname, widget_names='details.bootc')
        assert values
        assert values['details']['bootc']['details']['running_image'] == BOOTC_SWITCH_TARGET
        assert values['details']['bootc']['details']['rollback_image'] == BOOTC_BASE_IMAGE


def test_bootc_transient_install_warning(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Create a bootc host, and verify that all expected places warn you that package
    installs will be transient.

    :id: 10aea249-4e46-4e4f-a435-cff7e92afbdd

    :steps:
        1.Create and register a bootc host.
        2.Navigate to the All Hosts UI, and the Manage Packages and Manage Errata wizards.


    :expectedresults: In the 3 above cases, it is communicated to the user that package/errata actions will be transient.

    :Verifies: SAT-31251
    """
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Check the banner on the Content tab of All Hosts
        values = session.host_new.get_details(
            bootc_host.hostname, widget_names='content.transient_install_alert'
        )
        assert (
            values["content"]["transient_install_alert"]
            == 'Any updates to image mode host(s) will be lost on the next reboot.'
        )
        # Check the banner on the Manage Packages and Manage Errata wizards
        values = session.all_hosts.get_package_and_errata_wizard_review_hosts_text()
        banner_string = "Note that package actions on any image mode hosts will be transient and lost on the next reboot."
        assert banner_string in values[0]
        assert banner_string in values[1]


@pytest.mark.e2e
@pytest.mark.rhel_ver_list([10])
def test_positive_oscap_remediation_bootc(module_org, default_proxy, target_sat, bootc_host):
    """Run an OSCAP scan and remediate through WebUI on Bootc Host

    :id: 72ffdcca-ad7a-41ff-8c74-83969b740ab2

    :setup: scap content, scap policy, host group associated with the policy,

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

    :Verifies: SAT-31579
    """
    ak_name = f'ak_{gen_string("alpha")}_rhel10'
    cv_name = f'cv_{gen_string("alpha")}_rhel10'
    profile = OSCAP_PROFILE['cbrhel10']
    lifecycle_env = target_sat.api.LifecycleEnvironment(
        organization=module_org, name=gen_string('alpha')
    ).create()
    content_view = target_sat.api.ContentView(organization=module_org, name=cv_name).create()
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1, "CV not published"
    version = content_view.version[0].read()
    version.promote(data={'environment_ids': lifecycle_env.id, 'force': True})
    activation_key = target_sat.api.ActivationKey(
        name=ak_name,
        environment=lifecycle_env,
        content_view=content_view,
        organization=module_org,
    ).create()
    # Setup org for a custom repo for RHEL10
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.satclient_repo.rhel10,
            'organization-id': module_org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': lifecycle_env.id,
            'activationkey-id': activation_key.id,
        }
    )

    contenthost = bootc_host
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
            'content-view': cv_name,
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
        ak_name,
        target_sat,
        ignore_subman_errors=True,
        force=True,
        insecure=True,
        hostgroup=hostgroup,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    rhel_repo = settings.repos.rhel10_os
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

    # Workaround for bootc-container we use for testing, needs cron installed
    result = contenthost.execute("dnf install -y --transient rpm-cron")
    # Sleep is to give cron time to install
    time.sleep(5)
    assert result.status == 0
    result = contenthost.execute("sudo systemctl start crond")
    assert result.status == 0

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
        assert contenthost.execute("rpm -q aide").status == 0
