"""Test class foreman_rake

:Requirement: TasksPlugin

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:CaseImportance: Medium

:CaseComponent: TasksPlugin

:Team: Endeavour

:Upstream: No
"""
import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.tier3
def test_positive_katello_reimport(target_sat):
    """Close loop bug for running katello:reimport.  Making sure
    that katello:reimport works and doesn't throw an error.

    :id: b4119265-1bf0-4b0b-8b96-43f68af39708

    :Steps: Have satellite up and run 'foreman-rake katello:reimport'

    :expectedresults: Successfully reimport without errors

    :bz: 1771555

    :customerscenario: true
    """

    result = target_sat.execute('foreman-rake katello:reimport')
    assert 'NoMethodError:' not in result.stdout
    assert 'rake aborted!' not in result.stdout
