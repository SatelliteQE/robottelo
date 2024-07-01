"""Test module for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

import pytest


@pytest.mark.rhel_ver_list([9])
def test_positive_run_long_job(module_org, rex_contenthost, module_target_sat):
    """Run a long running job

    :id: 76934868-89e6-4eb6-905e-d0d5ededc077

    :expectedresults: Verify the long job was successfully ran and not terminated too soon

    :bz: 2270295

    :parametrized: yes
    """
    client = rex_contenthost
    invocation_command = module_target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': 'command=sleep 700',
            'search-query': f"name ~ {client.hostname}",
        },
        timeout='800s',
    )
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    try:
        assert result['success'] == '1'
    except AssertionError as err:
        raise AssertionError(
            'host output: {}'.format(
                ' '.join(
                    module_target_sat.cli.JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
        ) from err
