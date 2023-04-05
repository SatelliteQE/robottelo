"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^6].*')
def test_positive_ansible_e2e(target_sat, module_org, rhel_contenthost):
    """
    Test successful execution of Ansible Job on host.

    :id: 0c52bc63-a41a-4f48-a980-fe49b4ecdbdc

    :Steps:
        1. Register a content host with satellite
        2. Import a role into satellite
        3. Assign that role to a host
        4. Assert that the role and variable were assigned to the host successfully
        5. Run the Ansible playbook associated with that role
        6. Check if the job is executed successfully.
        7. Disassociate the Role from the host.
        8. Delete the assigned ansible role

    :expectedresults:
        1. Host should be assigned the proper role.
        2. Job execution must be successful.
        3. Operations performed with hammer must be successful.

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    SELECTED_ROLE_1 = 'theforeman.foreman_scap_client'
    SELECTED_VAR = gen_string('alpha')
    if rhel_contenthost.os_version.major <= 7:
        rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
        assert rhel_contenthost.execute('yum install -y insights-client').status == 0
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, force=True)
    assert rhel_contenthost.subscribed
    rhel_contenthost.add_rex_key(satellite=target_sat)
    proxy_id = target_sat.nailgun_smart_proxy.id
    target_host = rhel_contenthost.nailgun_host

    target_sat.cli.Ansible.roles_sync(
        {'role-names': f'{SELECTED_ROLE},{SELECTED_ROLE_1}', 'proxy-id': proxy_id}
    )

    result = target_sat.cli.Host.ansible_roles_add(
        {'id': target_host.id, 'ansible-role': SELECTED_ROLE}
    )
    assert 'Ansible role has been associated.' in result[0]['message']

    target_sat.cli.Ansible.variables_create(
        {'variable': SELECTED_VAR, 'ansible-role': SELECTED_ROLE}
    )

    assert SELECTED_ROLE, (
        SELECTED_VAR in target_sat.cli.Ansible.variables_info({'name': SELECTED_VAR}).stdout
    )
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Ansible Roles - Ansible Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    result = target_sat.cli.Host.ansible_roles_assign(
        {'id': target_host.id, 'ansible-roles': f'{SELECTED_ROLE},{SELECTED_ROLE_1}'}
    )
    assert 'Ansible roles were assigned to the host' in result[0]['message']

    result = target_sat.cli.Host.ansible_roles_remove(
        {'id': target_host.id, 'ansible-role': SELECTED_ROLE}
    )
    assert 'Ansible role has been disassociated.' in result[0]['message']

    result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
    assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']

    assert SELECTED_ROLE, (
        SELECTED_VAR not in target_sat.cli.Ansible.variables_info({'name': SELECTED_VAR}).stdout
    )


@pytest.mark.e2e
@pytest.mark.tier2
def test_add_and_remove_ansible_role_hostgroup(target_sat):
    """
    Test add and remove functionality for ansible roles in hostgroup via cli

    :id: 2c6fda14-4cd2-490a-b7ef-7a08f8164fad

    :customerscenario: true

    :Steps:
        1. Create a hostgroup
        2. Sync few ansible roles
        3. Assign a few ansible roles with the host group
        4. Add some ansible role with the host group
        5. Remove the added ansible roles from the host group

    :expectedresults:
        1. Ansible role assign/add/remove functionality should work as expected in cli

    :BZ: 2029402

    :CaseAutomation: Automated
    """
    ROLES = [
        'theforeman.foreman_scap_client',
        'redhat.satellite.hostgroups',
        'RedHatInsights.insights-client',
    ]
    proxy_id = target_sat.nailgun_smart_proxy.id
    hg_name = gen_string('alpha')
    result = target_sat.cli.HostGroup.create({'name': hg_name})
    assert result['name'] == hg_name
    target_sat.cli.Ansible.roles_sync({'role-names': ROLES, 'proxy-id': proxy_id})
    result = target_sat.cli.HostGroup.ansible_roles_assign(
        {'name': hg_name, 'ansible-roles': f'{ROLES[1]},{ROLES[2]}'}
    )
    assert 'Ansible roles were assigned to the hostgroup' in result[0]['message']
    result = target_sat.cli.HostGroup.ansible_roles_add({'name': hg_name, 'ansible-role': ROLES[0]})
    assert 'Ansible role has been associated.' in result[0]['message']
    result = target_sat.cli.HostGroup.ansible_roles_remove(
        {'name': hg_name, 'ansible-role': ROLES[0]}
    )
    assert 'Ansible role has been disassociated.' in result[0]['message']
