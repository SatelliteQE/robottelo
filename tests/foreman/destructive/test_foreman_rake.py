"""Test class foreman_rake

:Requirement: TasksPlugin

:CaseAutomation: Automated

:CaseImportance: Medium

:CaseComponent: TasksPlugin

:Team: Endeavour

"""
import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.tier3
def test_positive_katello_reimport(target_sat):
    """Close loop bug for running katello:reimport.  Making sure
    that katello:reimport works and doesn't throw an error.

    :id: b4119265-1bf0-4b0b-8b96-43f68af39708

    :steps: Have satellite up and run 'foreman-rake katello:reimport'

    :expectedresults: Successfully reimport without errors

    :bz: 1771555

    :customerscenario: true
    """

    result = target_sat.execute('foreman-rake katello:reimport')
    assert 'NoMethodError:' not in result.stdout
    assert 'rake aborted!' not in result.stdout
    assert result.status == 0


@pytest.mark.tier3
def test_positive_katello_correct_repositories(target_sat):
    """Make sure that foreman-rake katello:correct_repositories COMMIT=true works and doesn't throw an error.

    :id: 95816f1c-e028-40e7-be6d-5bf1269daf74

    :steps: Have satellite up and run the command

    :expectedresults: Successfully execute without errors

    """

    result = target_sat.execute('foreman-rake katello:correct_repositories COMMIT=true')
    assert result.status == 0
