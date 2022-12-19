"""Test for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.api.utils import wait_for_tasks
from robottelo.hosts import get_sat_version
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
        "Smart Proxy Upgrade Playbook" if is_open("BZ:2152951") else "Capsule Upgrade Playbook"
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
    feature_set = {feat['name'] for feat in result['features']}
    assert {'Ansible', 'Dynflow', 'Script', 'Pulpcore', 'Logs'}.issubset(feature_set)
