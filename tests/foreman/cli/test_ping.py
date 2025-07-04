"""Test Class for hammer ping

:Requirement: Ping

:CaseAutomation: Automated

:CaseComponent: Hammer

:Team: Rocket

:CaseImportance: Critical

"""

import pytest


@pytest.mark.pit_server
@pytest.mark.upgrade
@pytest.mark.parametrize('switch_user', [False, True], ids=['root', 'non-root'])
def test_positive_ping(target_sat, switch_user):
    """hammer ping return code

    :id: dfa3ab4f-a64f-4a96-8c7f-d940df22b8bf

    :steps:
        1. Execute hammer ping
        2. Check its return code, should be 0 if all services are ok else
           != 0

    :expectedresults: hammer ping returns a right return code

    :parametrized: yes

    :BZ: 2122176, 2115775

    :customerscenario: true
    """
    result = target_sat.execute(f"su - {'postgres' if switch_user else 'root'} -c 'hammer ping'")
    assert result.stderr == ''

    # Filter lines containing status
    statuses = [line for line in result.stdout.splitlines() if 'status:' in line.lower()]

    # Get count of total status lines and lines containing OK
    status_count = len(statuses)
    ok_count = len([status for status in statuses if status.split(':')[1].strip().lower() == 'ok'])

    if status_count == ok_count:
        assert result.status == 0, 'Return code should be 0 if all services are ok'
    else:
        assert result.status != 0, 'Return code should not be 0 if any service is not ok'
