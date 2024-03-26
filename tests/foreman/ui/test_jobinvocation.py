"""Test class for Job Invocation procedure

:Requirement: JobInvocation

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""
from inflection import camelize
import pytest

from robottelo.utils.datafactory import gen_string


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
        recent_jobs = session.host_new.get_details(hostname, "overview.recent_jobs")
        assert recent_jobs['overview']['recent_jobs']['finished']['table'][0]['column0'] == "Run ls"
        assert (
            recent_jobs['overview']['recent_jobs']['finished']['table'][0]['column2'] == "succeeded"
        )


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
