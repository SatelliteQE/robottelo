"""Test Class for hammer ping

:Requirement: Ping

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hammer

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest

from robottelo import ssh


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_ping():
    """hammer ping return code

    :id: dfa3ab4f-a64f-4a96-8c7f-d940df22b8bf

    :steps:
        1. Execute hammer ping
        2. Check its return code, should be 0 if all services are ok else
           != 0

    :expectedresults: hammer ping returns a right return code
    """
    result = ssh.command('hammer ping')
    assert result.stderr.decode() == ''

    status_count = 0
    ok_count = 0
    # Exclude message from stdout for services candlepin_events and katello_events
    result.stdout = [line for line in result.stdout if 'message' not in line]

    # iterate over the lines grouping every 3 lines
    # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
    # only the status line is relevant for this test
    for _, status, _ in zip(*[iter(result.stdout)] * 3):
        status_count += 1

        if status.split(':')[1].strip().lower() == 'ok':
            ok_count += 1

    if status_count == ok_count:
        assert result.return_code == 0, 'Return code should be 0 if all services are ok'
    else:
        assert result.return_code != 0, 'Return code should not be 0 if any service is not ok'
