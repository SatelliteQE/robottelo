"""Test for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.config import settings
from robottelo.hosts import get_sat_version
from robottelo.utils import ohsnap
from robottelo.utils.issue_handlers import is_open

CAPSULE_TARGET_VERSION = f'6.{get_sat_version().minor}.z'


@pytest.mark.tier4
def test_positive_run_capsule_upgrade_playbook(module_capsule_configured, target_sat):
    """Run Capsule Upgrade playbook against an External Capsule

    :id: 9ec6903d-2bb7-46a5-8002-afc74f06d83b

    :steps:
        1. Create a Capsule VM, add REX key.
        2. Run the Capsule Upgrade Playbook.

    :expectedresults: Capsule is upgraded successfully

    :BZ: 2152951

    :CaseImportance: Medium
    """
    template_name = (
        'Smart Proxy Upgrade Playbook' if is_open('BZ:2152951') else 'Capsule Upgrade Playbook'
    )
    template_id = (
        target_sat.api.JobTemplate().search(query={'search': f'name="{template_name}"'})[0].id
    )
    module_capsule_configured.add_rex_key(satellite=target_sat)
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'target_version': CAPSULE_TARGET_VERSION,
                'whitelist_options': 'repositories-validate,repositories-setup',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {module_capsule_configured.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    result = target_sat.execute('satellite-maintain health check')
    assert result.status == 0
    for line in result.stdout:
        assert 'FAIL' not in line
    result = target_sat.api.SmartProxy(
        id=target_sat.api.SmartProxy(name=target_sat.hostname).search()[0].id
    ).refresh()
    feature_set = {feat['name'] for feat in result['features']}
    assert {'Ansible', 'Dynflow', 'Script', 'Pulpcore', 'Logs'}.issubset(feature_set)


@pytest.mark.tier3
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^6].*')
def test_negative_time_to_pickup(
    module_org,
    module_target_sat,
    smart_proxy_location,
    module_ak_with_cv,
    module_capsule_configured_mqtt,
    rhel_contenthost,
):
    """Time to pickup setting is honored for host registered to mqtt

    :id: a082f599-fbf7-4779-aa18-5139e2bce774

    :expectedresults: Time to pickup aborts the job if mqtt client doesn't
        respond in time

    :CaseImportance: High

    :bz: 2158738, 2118651

    :parametrized: yes
    """
    client_repo = ohsnap.dogfood_repository(
        settings.ohsnap,
        product='client',
        repo='client',
        release='client',
        os_release=rhel_contenthost.os_version.major,
    )
    # Update module_capsule_configured_mqtt to include module_org/smart_proxy_location
    module_target_sat.cli.Capsule.update(
        {
            'name': module_capsule_configured_mqtt.hostname,
            'organization-ids': module_org.id,
            'location-ids': smart_proxy_location.id,
        }
    )
    # register host with pull provider rex
    result = rhel_contenthost.register(
        module_org,
        smart_proxy_location,
        module_ak_with_cv.name,
        target=module_capsule_configured_mqtt,
        satellite=module_target_sat,
        setup_remote_execution_pull=True,
        repo=client_repo.baseurl,
    )
    template_id = (
        module_target_sat.api.JobTemplate()
        .search(query={'search': 'name="Run Command - Script Default"'})[0]
        .id
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    # check mqtt client is running
    result = rhel_contenthost.execute('systemctl status yggdrasild')
    assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
    # check that longrunning command is not affected by time_to_pickup BZ#2158738
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'organization': module_org.name,
            'location': smart_proxy_location.name,
            'inputs': {
                'command': 'echo start; sleep 10; echo done',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
            'time_to_pickup': '5',
        },
    )
    module_target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    # stop yggdrasil client on host
    result = rhel_contenthost.execute('systemctl stop yggdrasild')
    assert result.status == 0, f'Failed to stop yggdrasil on client: {result.stderr}'

    # Make sure the job is executed by the registered-trough capsule
    global_ttp = module_target_sat.api.Setting().search(
        query={'search': 'name="remote_execution_global_proxy"'}
    )[0]
    global_ttp.value = False
    global_ttp.update(['value'])

    # run script provider rex command with time_to_pickup
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'organization': module_org.name,
            'location': smart_proxy_location.name,
            'inputs': {
                'command': 'ls -la',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
            'time_to_pickup': '10',
        },
    )
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', must_succeed=False
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.status_label == "failed"
    result = module_target_sat.api.ForemanTask().search(
        query={'search': f'resource_type = JobInvocation and resource_id = {job["id"]}'}
    )
    assert 'The job was not picked up in time' in result[0].humanized['output']

    # Check that global setting is applied
    global_ttp = module_target_sat.api.Setting().search(
        query={'search': 'name="remote_execution_time_to_pickup"'}
    )[0]
    global_ttp.value = '10'
    global_ttp.update(['value'])
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'organization': module_org.name,
            'location': smart_proxy_location.name,
            'inputs': {
                'command': 'ls -la',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
        },
    )
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', must_succeed=False
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.status_label == "failed"
    result = module_target_sat.api.ForemanTask().search(
        query={'search': f'resource_type = JobInvocation and resource_id = {job["id"]}'}
    )
    assert 'The job was not picked up in time' in result[0].humanized['output']
