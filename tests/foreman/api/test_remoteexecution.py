"""Test for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import client
from nailgun.entity_mixins import TaskFailedError

from robottelo.api.utils import wait_for_tasks


CAPSULE_TARGET_VERSION = '6.10.z'


@pytest.mark.tier4
def test_positive_run_capsule_upgrade_playbook(capsule_configured, target_sat):
    """Run Capsule Upgrade playbook against an External Capsule

    :id: 9ec6903d-2bb7-46a5-8002-afc74f06d83b

    :steps:
        1. Create a Capsule VM, add REX key.
        2. Run the Capsule Upgrade Playbook.

    :expectedresults: Capsule is upgraded successfully

    :CaseImportance: Medium
    """
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Capsule Upgrade Playbook"'})[0]
        .id
    )

    capsule_configured.add_rex_key(satellite=target_sat)
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'target_version': CAPSULE_TARGET_VERSION,
                'whitelist_options': 'repositories-validate,repositories-setup',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {capsule_configured.hostname}',
        },
    )
    wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    result = target_sat.execute('satellite-maintain health check')
    assert result.status == 0
    for line in result.stdout:
        assert 'FAIL' not in line

    result = target_sat.api.SmartProxy(
        id=target_sat.api.SmartProxy(name=target_sat.hostname).search()[0].id
    ).refresh()
    feature_list = [feat['name'] for feat in result['features']]
    assert {'Container_Gateway', 'Dynflow', 'SSH', 'Pulpcore', 'Templates'}.issubset(feature_list)


@pytest.mark.destructive
def test_negative_run_capsule_upgrade_playbook_on_satellite(target_sat):
    """Run Capsule Upgrade playbook against the Satellite itself

    :id: 99462a11-5133-415d-ba64-4354da539a34

    :steps:
        1. Add REX key to the Satellite server.
        2. Run the Capsule Upgrade Playbook.
        3. Check the job output for proper failure reason.

    :expectedresults: Should fail

    :CaseImportance: Medium
    """
    sat = target_sat.nailgun_host
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Capsule Upgrade Playbook"'})[0]
        .id
    )

    target_sat.add_rex_key(satellite=target_sat)
    with pytest.raises(TaskFailedError) as error:
        target_sat.api.JobInvocation().run(
            data={
                'job_template_id': template_id,
                'inputs': {
                    'target_version': CAPSULE_TARGET_VERSION,
                    'whitelist_options': "repositories-validqqate,repositories-setup",
                },
                'targeting_type': "static_query",
                'search_query': f"name = {sat.name}",
            }
        )
    assert 'A sub task failed' in error.value.args[0]
    job = target_sat.api.JobInvocation().search(
        query={'search': f'host={sat.name},status=failed,description="Capsule Upgrade Playbook"'}
    )[0]
    response = client.get(
        f'{target_sat.url}/api/job_invocations/{job.id}/hosts/{sat.id}',
        auth=(target_sat.username, target_sat.password),
        verify=False,
    )
    assert 'This playbook cannot be executed on a Satellite server.' in response.text
