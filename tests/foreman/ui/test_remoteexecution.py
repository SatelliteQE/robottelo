"""Test class for Job Invocation procedure

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""
import datetime
import time

from inflection import camelize
import pytest
from wait_for import wait_for

from robottelo.utils.datafactory import (
    gen_string,
)


@pytest.mark.rhel_ver_match('8')
def test_positive_run_default_job_template(
    session,
    target_sat,
    rex_contenthost,
    module_org,
):
    """Run a job template on a host

    :id: a21eac46-1a22-472d-b4ce-66097159a868

    :Setup: Use pre-defined job template.

    :steps:

        1. Get contenthost with rex enabled
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host, check also using the job widget on the main dashboard

    :parametrized: yes

    :bz: 1898656, 2182353

    :customerscenario: true
    """

    hostname = rex_contenthost.hostname

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        command = 'ls'
        session.jobinvocation.run(
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.targetting_type': 'Hosts',
                'target_hosts_and_inputs.targets': hostname,
                'target_hosts_and_inputs.command': command,
            }
        )
        session.jobinvocation.wait_job_invocation_state(entity_name='Run ls', host_name=hostname)
        status = session.jobinvocation.read(entity_name='Run ls', host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'

        # check status also on the job dashboard
        job_name = f'Run {command}'
        jobs = session.dashboard.read('LatestJobs')['jobs']
        success_jobs = [job for job in jobs if job['State'] == 'succeeded']
        assert len(success_jobs) > 0
        assert job_name in [job['Name'] for job in success_jobs]


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
@pytest.mark.parametrize(
    'ui_user', [{'admin': True}, {'admin': False}], indirect=True, ids=['adminuser', 'nonadminuser']
)
def test_positive_run_custom_job_template(
    session, module_org, default_location, target_sat, ui_user, rex_contenthost
):
    """Run a job template on a host

    :id: 3a59eb15-67c4-46e1-ba5f-203496ec0b0c

    :Setup: Create a working job template.

    :steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes

    :bz: 2220965

    :customerscenario: true
    """

    hostname = rex_contenthost.hostname
    ui_user.location.append(target_sat.api.Location(id=default_location.id))
    ui_user.update(['location'])
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


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.rhel_ver_list([8])
def test_positive_run_job_template_multiple_hosts(
    session, module_org, target_sat, rex_contenthosts
):
    """Run a job template against multiple hosts

    :id: c4439ec0-bb80-47f6-bc31-fa7193bfbeeb

    :Setup: Create a working job template.

    :steps:

        1. Set remote_execution_connect_by_ip on hosts to true
        2. Navigate to the hosts page and select at least two hosts
        3. Click the "Select Action"
        4. Select the job and appropriate template
        5. Run the job

    :expectedresults: Verify the job was successfully ran against the hosts
    """

    host_names = []
    for vm in rex_contenthosts:
        # for vm in rex_contenthost:
        host_names.append(vm.hostname)
        vm.configure_rex(satellite=target_sat, org=module_org)
    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        # session.location.select('Default Location')
        for host in host_names:
            assert session.host.search(host)[0]['Name'] == host
        session.host.reset_search()
        job_status = session.host.schedule_remote_job(
            host_names,
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.command': 'sleep 5',
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert {host_job['Host'] for host_job in job_status['overview']['hosts_table']} == set(
            host_names
        )
        assert all(
            host_job['Status'] == 'success' for host_job in job_status['overview']['hosts_table']
        )


@pytest.mark.rhel_ver_match('8')
@pytest.mark.tier3
def test_positive_run_scheduled_job_template_by_ip(session, module_org, rex_contenthost):
    """Schedule a job to be ran against a host by ip

    :id: 4387bed9-969d-45fb-80c2-b0905bb7f1bd

    :Setup: Use pre-defined job template.

    :steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Select "Schedule future execution"
        5. Enter a desired time for the job to run
        6. Click submit

    :expectedresults:

        1. Verify the job was not immediately ran
        2. Verify the job was successfully ran after the designated time

    :parametrized: yes
    """
    job_time = 6 * 60
    hostname = rex_contenthost.hostname
    with session:
        session.organization.select(module_org.name)
        session.location.select('Default Location')
        assert session.host.search(hostname)[0]['Name'] == hostname
        plan_time = session.browser.get_client_datetime() + datetime.timedelta(seconds=job_time)
        command_to_run = 'sleep 10'
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.command': command_to_run,
                'schedule.future': True,
                'schedule_future_execution.start_at_date': plan_time.strftime("%Y/%m/%d"),
                'schedule_future_execution.start_at_time': plan_time.strftime("%H:%M"),
            },
            wait_for_results=False,
        )
        # Note that to create this host scheduled job we spent some time from that plan_time, as it
        # was calculated before creating the job
        job_left_time = (plan_time - session.browser.get_client_datetime()).total_seconds()
        # assert that we have time left to wait, otherwise we have to use more job time,
        # the job_time must be significantly greater than job creation time.
        assert job_left_time > 0
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] in ('Awaiting start', 'N/A')
        # sleep 3/4 of the left time
        time.sleep(job_left_time * 3 / 4)
        job_status = session.jobinvocation.read(
            f'Run {command_to_run}', hostname, 'overview.hosts_table'
        )
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] in ('Awaiting start', 'N/A')
        # recalculate the job left time to be more accurate
        job_left_time = (plan_time - session.browser.get_client_datetime()).total_seconds()
        # the last read time should not take more than 1/4 of the last left time
        assert job_left_time > 0
        wait_for(
            lambda: session.jobinvocation.read(
                f'Run {command_to_run}', hostname, 'overview.hosts_table'
            )['overview']['hosts_table'][0]['Status']
            == 'running',
            timeout=(job_left_time + 30),
            delay=1,
        )
        # wait the job to change status to "success"
        wait_for(
            lambda: session.jobinvocation.read(
                f'Run {command_to_run}', hostname, 'overview.hosts_table'
            )['overview']['hosts_table'][0]['Status']
            == 'success',
            timeout=30,
            delay=1,
        )
        job_status = session.jobinvocation.read(f'Run {command_to_run}', hostname, 'overview')
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_job_check_mode(session):
    """Run a job on a host with enable_roles_check_mode parameter enabled

    :id: 7aeb7253-e555-4e28-977f-71f16d3c32e2

    :steps:

        1. Set the value of the ansible_roles_check_mode parameter to true on a host
        2. Associate one or more Ansible roles with the host
        3. Run Ansible roles against the host

    :expectedresults: Verify that the roles were run in check mode
                      (i.e. no changes were made on the host)

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-RemoteExecution

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_config_report_failed_tasks_errors(session):
    """Check that failed Ansible tasks show as errors in the config report

    :id: 1a91e534-143f-4f35-953a-7ad8b7d2ddf3

    :steps:

        1. Import Ansible roles
        2. Assign Ansible roles to a host
        3. Run Ansible roles on host

    :expectedresults: Verify that any task failures are listed as errors in the config report

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_config_report_changes_notice(session):
    """Check that Ansible tasks that make changes on a host show as notice in the config report

    :id: 8c90f179-8b70-4932-a477-75dc3566c437

    :steps:

        1. Import Ansible Roles
        2. Assign Ansible roles to a host
        3. Run Ansible Roles on a host

    :expectedresults: Verify that any tasks that make changes on the host
                      are listed as notice in the config report

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_variables_imported_with_roles(session):
    """Verify that, when Ansible roles are imported, their variables are imported simultaneously

    :id: 107c53e8-5a8a-4291-bbde-fbd66a0bb85e

    :steps:

        1. Import Ansible roles

    :expectedresults: Verify that any variables in the role were also imported to Satellite

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_roles_import_in_background(session):
    """Verify that importing roles does not create a popup that blocks the UI

    :id: 4f1c7b76-9c67-42b2-9a73-980ca1f05abc

    :steps:

        1. Import Ansible roles

    :expectedresults: Verify that the UI is accessible while roles are importing

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_roles_ignore_list(session):
    """Verify that the ignore list setting prevents selected roles from being available for import

    :id: 6fa1d8f0-b583-4a07-88eb-c9ae7fcd0219

    :steps:

        1. Add roles to the ignore list in Administer > Settings > Ansible
        2. Navigate to Configure > Roles

    :expectedresults: Verify that any roles on the ignore list are not available for import

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_ansible_variables_installed_with_collection(session):
    """Verify that installing an Ansible collection also imports
       any variables associated with the collection

    :id: 7ff88022-fe9b-482f-a6bb-3922036a1e1c

    :steps:

        1. Install an Ansible collection
        2. Navigate to Configure > Variables

    :expectedresults: Verify that any variables associated with the collection
                      are present on Configure > Variables

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_install_ansible_collection_via_job_invocation(session):
    """Verify that Ansible collections can be installed on hosts via job invocations

    :id: d4096aef-f6fc-41b6-ae56-d19b1f49cd42

    :steps:

        1. Enable a host for remote execution
        2. Navigate to Hosts > Schedule Remote Job
        3. Select "Ansible Galaxy" as the job category
        4. Select "Ansible Collection - Install from Galaxy" as the job template
        5. Enter a collection in the ansible_collections_list field
        6. Click "Submit"

    :expectedresults: The Ansible collection is successfully installed on the host

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-RemoteExecution

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_set_ansible_role_order_per_host(session):
    """Verify that role run order can be set and that this order is respected when roles are run

    :id: 24fbcd60-7cd1-46ff-86ac-16d6b436202c

    :steps:

        1. Enable a host for remote execution
        2. Navigate to Hosts > All Hosts > $hostname > Edit > Ansible Roles
        3. Assign more than one role to the host
        4. Use the drag-and-drop mechanism to change the order of the roles
        5. Run Ansible roles on the host

    :expectedresults: The roles are run in the specified order

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_set_ansible_role_order_per_hostgroup(session):
    """Verify that role run order can be set and that this order is respected when roles are run

    :id: 9eb5bc8e-081a-45b9-8751-f4220c944da6

    :steps:

        1. Enable a host for remote execution
        2. Create a host group
        3. Navigate to Configure > Host Groups > $hostgroup > Ansible Roles
        4. Assign more than one role to the host group
        5. Use the drag-and-drop mechanism to change the order of the roles
        6. Add the host to the host group
        7. Run Ansible roles on the host group

    :expectedresults: The roles are run in the specified order

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_matcher_field_highlight(session):
    """Verify that Ansible variable matcher fields change color when modified

    :id: 67b45cfe-31bb-41a8-b88e-27917c68f33e

    :steps:

        1. Navigate to Configure > Variables > $variablename
        2. Select the "Override" checkbox in the "Default Behavior" section
        3. Click "+Add Matcher" in the "Specify Matcher" section
        4. Select an option from the "Attribute type" dropdown
        5. Add text to the attribute type input field
        6. Add text to the "Value" input field

    :expectedresults: The background of each field turns yellow when a change is made

    :CaseAutomation: NotAutomated

    :CaseComponent: Ansible-ConfigurationManagement

    :Team: Rocket
    """


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
