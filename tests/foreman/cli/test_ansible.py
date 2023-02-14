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
    SELECTED_VAR = 'insights_variable'
    if rhel_contenthost.os_version.major <= 7:
        rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
        assert rhel_contenthost.execute('yum install -y insights-client').status == 0
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, force=True)
    assert rhel_contenthost.subscribed
    rhel_contenthost.add_rex_key(satellite=target_sat)
    proxy_id = target_sat.nailgun_smart_proxy.id
    target_host = rhel_contenthost.nailgun_host

    target_sat.cli.Ansible.roles_sync({'role-names': SELECTED_ROLE, 'proxy-id': proxy_id})

    target_sat.cli.Host.ansible_roles_assign({'id': target_host.id, 'ansible-roles': SELECTED_ROLE})

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

    result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
    assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']

    assert SELECTED_ROLE, (
        SELECTED_VAR not in target_sat.cli.Ansible.variables_info({'name': SELECTED_VAR}).stdout
    )
