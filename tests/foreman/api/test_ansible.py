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
from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings, user_nailgun_config
from robottelo.utils.issue_handlers import is_open


@pytest.mark.e2e
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
    proxy_id = target_sat.nailgun_smart_proxy.id
    playbook_fetch = target_sat.api.AnsiblePlaybooks().fetch(data={'proxy_id': proxy_id})
    playbooks_count = len(playbook_fetch['results']['playbooks_names'])
    playbook_sync = target_sat.api.AnsiblePlaybooks().sync(data={'proxy_id': proxy_id})
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
def test_positive_ansible_job_on_host(
    target_sat, module_org, module_location, module_ak_with_synced_repo, rhel_contenthost
):
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

    :BZ: 2164400

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    if rhel_contenthost.os_version.major <= 7:
        rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
        assert rhel_contenthost.execute('yum install -y insights-client').status == 0
    result = rhel_contenthost.register(
        module_org, module_location, module_ak_with_synced_repo.name, target_sat
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    proxy_id = target_sat.nailgun_smart_proxy.id
    target_host = rhel_contenthost.nailgun_host
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]})
    role_id = target_sat.api.AnsibleRoles().search(query={'search': f'name={SELECTED_ROLE}'})[0].id
    target_sat.api.Host(id=target_host.id).add_ansible_role(data={'ansible_role_id': role_id})
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
    target_sat.api.Host(id=target_host.id).remove_ansible_role(data={'ansible_role_id': role_id})
    host_roles = target_host.list_ansible_roles()
    assert len(host_roles) == 0


@pytest.mark.no_containers
def test_positive_ansible_job_on_multiple_host(
    target_sat,
    module_org,
    rhel9_contenthost,
    rhel8_contenthost,
    rhel7_contenthost,
    module_location,
    module_ak_with_synced_repo,
):
    """Test execution of Ansible job on multiple hosts simultaneously.

    :id: 9369feef-466c-40d3-9d0d-65520d7f21ef

    :customerscenario: true

    :steps:
        1. Register multiple content hosts with satellite
        2. Import a role into satellite
        3. Assign that role to all host
        4. Trigger ansible job keeping all host in a single query
        5. Check the passing and failing of individual hosts
        6. Check if one of the job on a host is failed resulting into whole job is marked as failed.

    :expectedresults:
        1. One of the jobs failing on a single host must impact the overall result as failed.

    :BZ: 2167396, 2190464, 2184117

    :CaseAutomation: Automated
    """
    hosts = [rhel9_contenthost, rhel8_contenthost, rhel7_contenthost]
    SELECTED_ROLE = 'RedHatInsights.insights-client'
    for host in hosts:
        result = host.register(
            module_org, module_location, module_ak_with_synced_repo.name, target_sat
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_host = host.nailgun_host
        target_sat.api.AnsibleRoles().sync(
            data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]}
        )
        role_id = (
            target_sat.api.AnsibleRoles().search(query={'search': f'name={SELECTED_ROLE}'})[0].id
        )
        target_sat.api.Host(id=target_host.id).add_ansible_role(data={'ansible_role_id': role_id})
        host_roles = target_host.list_ansible_roles()
        assert host_roles[0]['name'] == SELECTED_ROLE

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
            'search_query': f'name ^ ({hosts[0].hostname} && {hosts[1].hostname} '
            f'&& {hosts[2].hostname})',
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}',
        poll_timeout=1000,
        must_succeed=False,
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 2  # SELECTED_ROLE working on rhel8/rhel9 clients
    assert result.failed == 1  # SELECTED_ROLE failing  on rhel7 client
    assert result.status_label == 'failed'


@pytest.mark.e2e
@pytest.mark.tier2
def test_add_and_remove_ansible_role_hostgroup(target_sat):
    """
    Test add and remove functionality for ansible roles in hostgroup via API

    :id: 7672cf86-fa31-11ed-855a-0fd307d2d66b

    :Steps:
        1. Create a hostgroup
        2. Sync few ansible roles
        3. Assign a few ansible roles with the host group
        4. Add some ansible role with the host group
        5. Remove the added ansible roles from the host group

    :expectedresults:
        1. Ansible role assign/add/remove functionality should work as expected in API

    :BZ: 2164400
    """
    ROLE_NAMES = [
        'theforeman.foreman_scap_client',
        'redhat.satellite.hostgroups',
        'RedHatInsights.insights-client',
    ]
    hg = target_sat.api.HostGroup(name=gen_string('alpha')).create()
    proxy_id = target_sat.nailgun_smart_proxy.id
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': proxy_id, 'role_names': ROLE_NAMES})
    ROLES = [
        target_sat.api.AnsibleRoles().search(query={'search': f'name={role}'})[0].id
        for role in ROLE_NAMES
    ]
    target_sat.api.HostGroup(id=hg.id).assign_ansible_roles(data={'ansible_role_ids': ROLES[:2]})
    for r1, r2 in zip(target_sat.api.HostGroup(id=hg.id).list_ansible_roles(), ROLE_NAMES[:2]):
        assert r1['name'] == r2
    target_sat.api.HostGroup(id=hg.id).add_ansible_role(data={'ansible_role_id': ROLES[2]})
    for r1, r2 in zip(target_sat.api.HostGroup(id=hg.id).list_ansible_roles(), ROLE_NAMES):
        assert r1['name'] == r2

    for role in ROLES:
        target_sat.api.HostGroup(id=hg.id).remove_ansible_role(data={'ansible_role_id': role})
    host_roles = target_sat.api.HostGroup(id=hg.id).list_ansible_roles()
    assert len(host_roles) == 0


@pytest.fixture
def filtered_user(target_sat, module_org, module_location):
    """
    :Steps:
        1. Create a role with a host view filtered
        2. Create a user with that role
        3. Setup a host
    """
    api = target_sat.api
    role = api.Role(
        name=gen_string('alpha'), location=[module_location], organization=[module_org]
    ).create()
    # assign view_hosts (with a filter, to test BZ 1699188),
    # view_hostgroups, view_facts permissions to the role
    permission_hosts = api.Permission().search(query={'search': 'name="view_hosts"'})
    permission_hostgroups = api.Permission().search(query={'search': 'name="view_hostgroups"'})
    permission_facts = api.Permission().search(query={'search': 'name="view_facts"'})
    api.Filter(permission=permission_hosts, search='name != nonexistent', role=role).create()
    api.Filter(permission=permission_hostgroups, role=role).create()
    api.Filter(permission=permission_facts, role=role).create()

    password = gen_string('alpha')
    user = api.User(
        role=[role], password=password, location=[module_location], organization=[module_org]
    ).create()

    return user, password


@pytest.fixture
def rex_host_in_org_and_loc(target_sat, module_org, module_location, rex_contenthost):
    api = target_sat.api
    host = api.Host().search(query={'search': f'name={rex_contenthost.hostname}'})[0]
    host_id = host.id
    api.Host(id=host_id, organization=[module_org.id]).update(['organization'])
    api.Host(id=host_id, location=module_location.id).update(['location'])
    return host


@pytest.mark.rhel_ver_match('[78]')
@pytest.mark.tier2
def test_positive_read_facts_with_filter(
    target_sat, rex_contenthost, filtered_user, rex_host_in_org_and_loc
):
    """
    Read host's Ansible facts as a user with a role that has host filter

    :id: 483d5faf-7a4c-4cb7-b14f-369768ad99b0

        1. Run Ansible roles on a host
        2. Using API, read Ansible facts of that host

    :expectedresults: Ansible facts returned

    :BZ: 1699188

    :customerscenario: true
    """
    user, password = filtered_user
    host = rex_host_in_org_and_loc

    # gather ansible facts by running ansible roles on the host
    host.play_ansible_roles()
    if is_open('BZ:2216471'):
        host_wait = target_sat.api.Host().search(
            query={'search': f'name={rex_contenthost.hostname}'}
        )[0]
        wait_for(
            lambda: len(host_wait.get_facts()) > 0,
            timeout=30,
            delay=2,
        )

    user_cfg = user_nailgun_config(user.login, password)
    host = target_sat.api.Host(server_config=user_cfg).search(
        query={'search': f'name={rex_contenthost.hostname}'}
    )[0]
    # get facts through API
    facts = host.get_facts()
    assert 'subtotal' in facts
    assert facts['subtotal'] == 1
    assert 'results' in facts
    assert rex_contenthost.hostname in facts['results']
    assert len(facts['results'][rex_contenthost.hostname]) > 0
