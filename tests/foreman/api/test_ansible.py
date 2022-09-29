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


def test_positive_assign_ansible_role(target_sat):
    """
    Test API for assigning an Ansible Role to a host

    :id: 95d0213e-a5a9-4671-8a9e-89a77fc67f39

    :steps:
        1. Create a Host
        2. Import a roles into satellite
        3. Assign that role to a host
        4. Assert that the role was assigned to the host successfully

    :expectedresults:
        1. Host should be assigned the proper role.

    :CaseAutomation: Automated
    """
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    host = target_sat.api.Host().create()
    id = target_sat.internal_capsule.id
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': id, 'role_names': [SELECTED_ROLE]})
    host.assign_ansible_roles(data={'ansible_role_ids': [1]})
    host_roles = host.list_ansible_roles()
    assert host_roles[0]['name'] == SELECTED_ROLE
