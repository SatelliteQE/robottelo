"""Test class for Job Invocation procedure

:Requirement: JobInvocation

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from inflection import camelize

from robottelo.utils.datafactory import gen_string


@pytest.fixture
def module_rhel_client_by_ip(module_org, smart_proxy_location, rhel7_contenthost, target_sat):
    """Setup a broker rhel client to be used in remote execution by ip"""
    rhel7_contenthost.configure_rex(satellite=target_sat, org=module_org)
    target_sat.update_vm_host_location(rhel7_contenthost, location_id=smart_proxy_location.id)
    yield rhel7_contenthost


@pytest.mark.tier4
def test_positive_run_default_job_template_by_ip(
    session, module_org, smart_proxy_location, module_rhel_client_by_ip
):
    """Run a job template on a host connected by ip

    :id: 9a90aa9a-00b4-460e-b7e6-250360ee8e4d

    :Setup: Use pre-defined job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes

    :CaseLevel: System
    """
    hostname = module_rhel_client_by_ip.hostname
    with session:
        session.organization.select(module_org.name)
        session.location.select(smart_proxy_location.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        session.jobinvocation.run(
            {
                'job_category': 'Commands',
                'job_template': 'Run Command - Script Default',
                'search_query': f'name ^ {hostname}',
                'template_content.command': 'ls',
            }
        )
        session.jobinvocation.wait_job_invocation_state(entity_name='Run ls', host_name=hostname)
        status = session.jobinvocation.read(entity_name='Run ls', host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.tier4
def test_positive_run_custom_job_template_by_ip(
    session, module_org, smart_proxy_location, module_rhel_client_by_ip
):
    """Run a job template on a host connected by ip

    :id: e283ae09-8b14-4ce1-9a76-c1bbd511d58c

    :Setup: Create a working job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes

    :CaseLevel: System
    """
    hostname = module_rhel_client_by_ip.hostname
    job_template_name = gen_string('alpha')
    with session:
        session.organization.select(module_org.name)
        session.location.select(smart_proxy_location.name)
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
                'job_category': 'Miscellaneous',
                'job_template': job_template_name,
                'search_query': f'name ^ {hostname}',
                'template_content.command': 'ls',
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

    :caseComponent: Ansible

    :Team: Rocket

    :Steps:
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

    :caseComponent: Ansible

    :Team: Rocket

    :Steps:
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
