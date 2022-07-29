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
from fauxfactory import gen_string
from nailgun import client
from nailgun.entity_mixins import TaskFailedError


CAPSULE_TARGET_VERSION = '6.10.z'

pytestmark = pytest.mark.destructive


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


@pytest.mark.rhel_ver_list([7])
def test_positive_use_alternate_directory(rex_contenthost, target_sat):
    """Use alternate working directory on client to execute rex jobs

    :id: a0181f18-d3dc-4bd9-a2a6-430c2a49809e

    :expectedresults: Verify the job was successfully ran against the host

    :customerscenario: true

    :parametrized: yes
    """
    client = rex_contenthost
    testdir = gen_string('alpha')
    result = client.run(f'mkdir /{testdir}')
    assert result.status == 0
    result = client.run(f'chcon --reference=/var /{testdir}')
    assert result.status == 0
    result = target_sat.execute(
        f"sed -i r's/^:remote_working_dir:.*/:remote_working_dir: \\/{testdir}/' \
        /etc/foreman-proxy/settings.d/remote_execution_ssh.yml",
    )
    assert result.status == 0
    result = target_sat.execute('systemctl restart foreman-proxy')
    assert result.status == 0

    command = f'echo {gen_string("alpha")}'
    invocation_command = target_sat.cli_factory.make_job_invocation(
        {
            'job-template': 'Run Command - SSH Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {client.hostname}",
        }
    )
    result = target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    try:
        assert result['success'] == '1'
    except AssertionError:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output(
                {'id': invocation_command['id'], 'host': client.hostname}
            )
        )
        result = f'host output: {output}'
        raise AssertionError(result)

    task = target_sat.cli.Task.list_tasks({'search': command})[0]
    search = target_sat.cli.Task.list_tasks({'search': f'id={task["id"]}'})
    assert search[0]['action'] == task['action']
