"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""
import datetime
import time

import pytest
from wait_for import wait_for

from robottelo.utils.datafactory import gen_string


@pytest.mark.skip_if_open('BZ:2182353')
@pytest.mark.rhel_ver_match('8')
@pytest.mark.tier3
def test_positive_run_default_job_template_by_ip(session, rex_contenthost, module_org):
    """Run a job template against a single host by ip

    :id: a21eac46-1a22-472d-b4ce-66097159a868

    :Setup: Use pre-defined job template.

    :steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :parametrized: yes

    :bz: 1898656

    :customerscenario: true
    """
    hostname = rex_contenthost.hostname
    with session:
        session.organization.select(module_org.name)
        session.location.select('Default Location')
        assert session.host.search(hostname)[0]['Name'] == hostname
        command = 'ls'
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.command': command,
                'advanced_fields.execution_order_randomized': True,
                'schedule.immediate': True,
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['execution_order'] == 'Execution order: randomized'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'

        # check status also on the job dashboard
        job_name = f'Run {command}'
        jobs = session.dashboard.read('LatestJobs')['jobs']
        success_jobs = [job for job in jobs if job['State'] == 'succeeded']
        assert len(success_jobs) > 0
        assert job_name in [job['Name'] for job in success_jobs]


@pytest.mark.skip_if_open('BZ:2182353')
@pytest.mark.rhel_ver_match('8')
@pytest.mark.tier3
def test_positive_run_custom_job_template_by_ip(session, module_org, rex_contenthost):
    """Run a job template on a host connected by ip

    :id: 3a59eb15-67c4-46e1-ba5f-203496ec0b0c

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
    with session:
        session.organization.select(module_org.name)
        session.location.select('Default Location')
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
        assert session.host.search(hostname)[0]['Name'] == hostname
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'category_and_template.job_category': 'Miscellaneous',
                'category_and_template.job_template': job_template_name,
                'target_hosts_and_inputs.command': 'ls',
                'schedule.immediate': True,
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.skip_if_open('BZ:2182353')
@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.rhel_ver_list([8])
def test_positive_run_job_template_multiple_hosts_by_ip(
    session, module_org, target_sat, registered_hosts
):
    """Run a job template against multiple hosts by ip

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
    for vm in registered_hosts:
        host_names.append(vm.hostname)
        vm.configure_rex(satellite=target_sat, org=module_org)
    with session:
        session.organization.select(module_org.name)
        session.location.select('Default Location')
        hosts = session.host.search(' or '.join([f'name="{hostname}"' for hostname in host_names]))
        assert {host['Name'] for host in hosts} == set(host_names)
        job_status = session.host.schedule_remote_job(
            host_names,
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.command': 'ls',
                'schedule.immediate': True,
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert {host_job['Host'] for host_job in job_status['overview']['hosts_table']} == set(
            host_names
        )
        assert all(
            host_job['Status'] == 'success' for host_job in job_status['overview']['hosts_table']
        )


@pytest.mark.skip_if_open('BZ:2182353')
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
    job_time = 10 * 60
    hostname = rex_contenthost.hostname
    with session:
        session.organization.select(module_org.name)
        session.location.select('Default Location')
        assert session.host.search(hostname)[0]['Name'] == hostname
        plan_time = session.browser.get_client_datetime() + datetime.timedelta(seconds=job_time)
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'category_and_template.job_category': 'Commands',
                'category_and_template.job_template': 'Run Command - Script Default',
                'target_hosts_and_inputs.command': 'ls',
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
        assert job_status['overview']['hosts_table'][0]['Status'] == 'N/A'
        # sleep 3/4 of the left time
        time.sleep(job_left_time * 3 / 4)
        job_status = session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'N/A'
        # recalculate the job left time to be more accurate
        job_left_time = (plan_time - session.browser.get_client_datetime()).total_seconds()
        # the last read time should not take more than 1/4 of the last left time
        assert job_left_time > 0
        wait_for(
            lambda: session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')[
                'overview'
            ]['hosts_table'][0]['Status']
            == 'running',
            timeout=(job_left_time + 30),
            delay=1,
        )
        # wait the job to change status to "success"
        wait_for(
            lambda: session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')[
                'overview'
            ]['hosts_table'][0]['Status']
            == 'success',
            timeout=30,
            delay=1,
        )
        job_status = session.jobinvocation.read('Run ls', hostname, 'overview')
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'
