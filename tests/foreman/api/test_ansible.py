"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Ansible

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.config import settings


def test_fetch_and_sync_ansible_playbooks(target_sat):
    """
    Test Ansible Playbooks api for fetching and syncing playbooks

    :id: 17b4e767-1494-4960-bc60-f31a0495c09f

    :customerscenario: true

    :Steps:

        1. Install ansible collection with playbooks.
        2. Try to fetch the playbooks via api.
        3. Sync the playbooks.
        4. Assert the count of playbooks fetched and synced are equal.

    :expectedresults:
        1. Playbooks should be fetched and synced successfully.

    :BZ: 2115686

    :CaseAutomation: Automated
    """
    target_sat.execute(
        "ansible-galaxy collection install -p /usr/share/ansible/collections "
        "xprazak2.forklift_collection"
    )
    id = target_sat.api.SmartProxy(name=target_sat.hostname).search()[0].id
    playbook_fetch = target_sat.api.AnsiblePlaybooks().fetch(data={'proxy_id': id})
    playbooks_count = len(playbook_fetch['results']['playbooks_names'])
    playbook_sync = target_sat.api.AnsiblePlaybooks().sync(data={'proxy_id': id})
    assert playbook_sync['action'] == "Sync playbooks"

    target_sat.wait_for_tasks(
        search_query=(f'id = {playbook_sync["id"]}'),
        poll_timeout=100,
    )
    task_details = target_sat.api.ForemanTask().search(
        query={'search': f'id = {playbook_sync["id"]}'}
    )
    assert task_details[0].result == 'success'
    assert len(task_details[0].output['result']['created']) == playbooks_count


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^6].*')
def test_positive_ansible_job_on_host(target_sat, module_org, rhel_contenthost):
    """
    Test successful execution of Ansible Job on host.

    :id: c8dcdc54-cb98-4b24-bff9-049a6cc36acb

    :Steps:
        1. Register a content host with satellite
        2. Import a role into satellite
        3. Assign that role to a host
        4. Assert that the role was assigned to the host successfully
        5. Run the Ansible playbook associated with that role
        6. Check if the job is executed.

    :expectedresults:
        1. Host should be assigned the proper role.
        2. Job execution must be successful.

    :CaseAutomation: Automated
    """
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    if rhel_contenthost.os_version.major <= 7:
        rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
        assert rhel_contenthost.execute('yum install -y insights-client').status == 0
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, force=True)
    assert rhel_contenthost.subscribed
    rhel_contenthost.add_rex_key(satellite=target_sat)
    id = target_sat.nailgun_smart_proxy.id
    target_host = rhel_contenthost.nailgun_host
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': id, 'role_names': [SELECTED_ROLE]})
    target_host.assign_ansible_roles(data={'ansible_role_ids': [1]})
    host_roles = target_host.list_ansible_roles()
    assert host_roles[0]['name'] == SELECTED_ROLE
    assert target_host.name == rhel_contenthost.hostname
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
