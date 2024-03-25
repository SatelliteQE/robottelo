"""Test class for Job Invocation procedure

:Requirement: JobInvocation

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""
from collections import OrderedDict

from inflection import camelize
import pytest

from robottelo.utils.datafactory import (
    gen_string,
    valid_hostgroups_list_short,
)


@pytest.mark.tier4
def test_positive_hostgroups_full_nested_names(
    module_org,
    smart_proxy_location,
    target_sat,
):
    """Check that full host group names are displayed when invoking a job

    :id: 2301cd1d-ed82-4168-9f9b-d1661ac8fc5b

    :steps:

        1. Go to Monitor -> Jobs -> Run job
        2. In "Target hosts and inputs" step, choose "Host groups" targeting

    :expectedresults: Verify that in the dropdown, full hostgroup names are present, e.g. Parent/Child/Grandchild

    :parametrized: yes

    :customerscenario: true

    :BZ: 2209968
    """
    names = valid_hostgroups_list_short()
    tree = OrderedDict(
        {
            'parent1': {'name': names[0], 'parent': None},
            'parent2': {'name': names[1], 'parent': None},
            'child1a': {'name': names[2], 'parent': 'parent1'},
            'child1b': {'name': names[3], 'parent': 'parent1'},
            'child2': {'name': names[4], 'parent': 'parent2'},
            'grandchild1a1': {'name': names[5], 'parent': 'child1a'},
            'grandchild1a2': {'name': names[6], 'parent': 'child1a'},
            'grandchild1b': {'name': names[7], 'parent': 'child1b'},
        }
    )
    expected_names = []
    for identifier, data in tree.items():
        name = data['name']
        parent_name = None if data['parent'] is None else tree[data['parent']]['name']
        target_sat.cli_factory.hostgroup(
            {
                'name': name,
                'parent': parent_name,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        expected_name = ''
        current = identifier
        while current:
            expected_name = (
                f"{tree[current]['name']}/{expected_name}"
                if expected_name
                else tree[current]['name']
            )
            current = tree[current]['parent']
        # we should have something like "parent1/child1a"
        expected_names.append(expected_name)

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(smart_proxy_location.name)
        hostgroups = session.jobinvocation.read_hostgroups()

    for name in expected_names:
        assert name in hostgroups


@pytest.mark.rhel_ver_match('8')
def test_positive_run_default_job_template(
    session,
    target_sat,
    rex_contenthost,
    module_org,
):
    """Run a job template on a host connected by ip

    :id: 9a90aa9a-00b4-460e-b7e6-250360ee8e4d

    :Setup: Use pre-defined job template.

    :steps:

        1. Get contenthost with rex enabled
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes
    """

    hostname = rex_contenthost.hostname

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        session.jobinvocation.run(
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.targetting_type': 'Hosts',
                'target_hosts_and_inputs.targets': hostname,
                'target_hosts_and_inputs.command': 'ls',
            }
        )
        session.jobinvocation.wait_job_invocation_state(entity_name='Run ls', host_name=hostname)
        status = session.jobinvocation.read(entity_name='Run ls', host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
def test_rex_through_host_details(session, target_sat, rex_contenthost, module_org):
    """Run remote execution using the new host details page

    :id: ee625595-4995-43b2-9e6d-633c9b33ff93

    :steps:
        1. Navigate to Overview tab
        2. Schedule a job
        3. Wait for the job to finish
        4. Job is visible in Recent jobs card

    :expectedresults: Remote execution succeeded and the job is visible on Recent jobs card on
        Overview tab
    """

    hostname = rex_contenthost.hostname

    job_args = {
        'category_and_template.job_category': 'Commands',
        'category_and_template.job_template': 'Run Command - Script Default',
        'target_hosts_and_inputs.command': 'ls',
    }
    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.host_new.schedule_job(hostname, job_args)
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run ls on {hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        recent_jobs = session.host_new.get_details(hostname, "overview.recent_jobs")['overview']
        assert recent_jobs['recent_jobs']['finished']['table'][0]['column0'] == "Run ls"
        assert recent_jobs['recent_jobs']['finished']['table'][0]['column2'] == "succeeded"


@pytest.mark.tier4
@pytest.mark.rhel_ver_match('8')
def test_positive_run_custom_job_template(session, module_org, target_sat, rex_contenthost):
    """Run a job template on a host connected by ip

    :id: e283ae09-8b14-4ce1-9a76-c1bbd511d58c

    :Setup: Create a working job template.

    :steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes
    """

    hostname = rex_contenthost.hostname

    job_template_name = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        session.jobtemplate.create(
            {
                'template.name': job_template_name,
                'template.template_editor.rendering_options': 'Editor',
                'template.template_editor.editor': '<%= input("command") %>',
                'job.provider_type': 'Script',
                'inputs': [{'name': 'command', 'required': True, 'input_type': 'User input'}],
            }
        )
        assert session.jobtemplate.search(job_template_name)[0]['Name'] == job_template_name
        session.jobinvocation.run(
            {
                'category_and_template.job_category': 'Miscellaneous',
                'category_and_template.job_template': job_template_name,
                'target_hosts_and_inputs.targets': hostname,
                'target_hosts_and_inputs.command': 'ls',
            }
        )
        job_description = f'{camelize(job_template_name.lower())} with inputs command="ls"'
        session.jobinvocation.wait_job_invocation_state(
            entity_name=job_description, host_name=hostname
        )
        status = session.jobinvocation.read(entity_name=job_description, host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_schedule_recurring_host_job(self):
    """Using the new Host UI, schedule a recurring job on a Host

    :id: 5052be04-28ab-4349-8bee-851ef76e4ffa

    :caseComponent: Ansible-RemoteExecution

    :Team: Rocket

    :steps:
        1. Register a RHEL host to Satellite.
        2. Import all roles available by default.
        3. Assign a role to host.
        4. Navigate to the new UI for the given Host.
        5. Select the Jobs subtab.
        6. Click the Schedule Recurring Job button, and using the popup, schedule a
            recurring Job.
        7. Navigate to Job Invocations.

    :expectedresults: The scheduled Job appears in the Job Invocation list at the appointed
        time
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_schedule_recurring_hostgroup_job(self):
    """Using the new recurring job scheduler, schedule a recurring job on a Hostgroup

    :id: c65db99b-11fe-4a32-89d0-0a4692b07efe

    :caseComponent: Ansible-RemoteExecution

    :Team: Rocket

    :steps:
        1. Register a RHEL host to Satellite.
        2. Import all roles available by default.
        3. Assign a role to host.
        4. Navigate to the Host Group page.
        5. Select the "Configure Ansible Job" action.
        6. Click the Schedule Recurring Job button, and using the popup, schedule a
            recurring Job.
        7. Navigate to Job Invocations.

    :expectedresults: The scheduled Job appears in the Job Invocation list at the appointed
        time
    """
