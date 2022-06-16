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

pytestmark = pytest.mark.destructive


def test_negative_ping_fail_status_code(target_sat):
    """Negative test to verify non-zero status code of ping fail

    :id: 8f8675aa-df52-11eb-9353-b0a460e02491

    :customerscenario: true

    :BZ: 1941240

    :CaseImportance: Critical

    :expectedresults: Hammer ping fails and returns non-zero(1) status code.

    """
    command_out = target_sat.execute('satellite-maintain service stop --only tomcat.service')
    assert command_out.status == 0
    result = target_sat.execute("hammer ping")
    assert result.status == 1
    command_out = target_sat.execute('satellite-maintain service start --only tomcat.service')
    assert command_out.status == 0
