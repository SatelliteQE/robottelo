"""Test for Remote Execution

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import client
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError

from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.vm_capsule import CapsuleVirtualMachine


CAPSULE_TARGET_VERSION = '6.9.z'


@pytest.mark.tier4
@pytest.mark.libvirt_content_host
def test_positive_run_capsule_upgrade_playbook():
    """Run Capsule Upgrade playbook against an External Capsule

    :id: 9ec6903d-2bb7-46a5-8002-afc74f06d83b

    :steps:
        1. Create a Capsule VM, add REX key.
        2. Run the Capsule Upgrade Playbook.

    :expectedresults: Capsule is upgraded successfully

    :CaseImportance: Medium
    """
    with CapsuleVirtualMachine() as capsule_vm:
        template_id = (
            entities.JobTemplate()
            .search(query={'search': 'name="Capsule Upgrade Playbook"'})[0]
            .id
        )

        add_remote_execution_ssh_key(capsule_vm.ip_addr)
        job = entities.JobInvocation().run(
            synchronous=False,
            data={
                'job_template_id': template_id,
                'inputs': {
                    'target_version': CAPSULE_TARGET_VERSION,
                    'whitelist_options': "repositories-validate,repositories-setup",
                },
                'targeting_type': "static_query",
                'search_query': f"name = {capsule_vm.hostname}",
            },
        )
        wait_for_tasks(f"resource_type = JobInvocation and resource_id = {job['id']}")
        result = entities.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1

        result = capsule_vm.run('foreman-maintain health check')
        assert result.return_code == 0
        for line in result.stdout:
            assert 'FAIL' not in line

        result = entities.SmartProxy(
            id=entities.SmartProxy(name=capsule_vm.hostname).search()[0].id
        ).refresh()
        feature_list = [feat['name'] for feat in result['features']]
        assert {'Discovery', 'Dynflow', 'Ansible', 'SSH', 'Logs', 'Pulp'}.issubset(feature_list)


@pytest.mark.destructive
def test_negative_run_capsule_upgrade_playbook_on_satellite(default_org):
    """Run Capsule Upgrade playbook against the Satellite itself

    :id: 99462a11-5133-415d-ba64-4354da539a34

    :steps:
        1. Add REX key to the Satellite server.
        2. Run the Capsule Upgrade Playbook.
        3. Check the job output for proper failure reason.

    :expectedresults: Should fail

    :CaseImportance: Medium
    """
    sat = entities.Host().search(query={'search': f'name={settings.server.hostname}'})[0].read()
    template_id = (
        entities.JobTemplate().search(query={'search': 'name="Capsule Upgrade Playbook"'})[0].id
    )

    add_remote_execution_ssh_key(sat.name)
    with pytest.raises(TaskFailedError) as error:
        entities.JobInvocation().run(
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
    job = entities.JobInvocation().search(
        query={'search': f'host={sat.name},status=failed,description="Capsule Upgrade Playbook"'}
    )[0]
    response = client.get(
        f'https://{sat.name}/api/job_invocations/{job.id}/hosts/{sat.id}',
        auth=settings.server.get_credentials(),
        verify=False,
    )
    assert 'This playbook cannot be executed on a Satellite server.' in response.text
