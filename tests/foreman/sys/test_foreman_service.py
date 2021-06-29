"""Test class Foreman Service Integration with Apache

:Requirement: Other

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import pytest

from robottelo.constants import DEFAULT_ORG


@pytest.mark.destructive
@pytest.mark.run_in_one_thread
@pytest.mark.upgrade
def test_positive_foreman_service_auto_restart(foreman_service_teardown):
    """Foreman Service should get auto-restarted in case it is halted or stopped for some reason

    :CaseComponent: Infrastructure

    :Assignee: lpramuk

    :id: 766560b8-30bb-11eb-8dae-d46d6dd3b5b2

    :Steps:
        1. Stop the Foreman Service
        2. Make any API call to Satellite

    :expectedresults: Foreman Service should get restarted automatically
    """
    sat = foreman_service_teardown
    sat.execute('systemctl stop foreman')
    result = sat.execute('foreman-maintain service status --only=foreman')
    assert result.status == 1
    assert 'not running (foreman)' in result.stdout
    assert sat.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
    sat.execute('foreman-maintain service status --only=foreman')
