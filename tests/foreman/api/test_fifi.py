"""Test FiFi

There is a test in Robottelo, tests/foreman/ui/test_remoteexecution.py, that tests
Satellite part of FiFi (Receptor installation) as end-to-end as possible. However,
it doesn't test cloud.redhat.com, we chose to use IQE framework to run tests that need to
do that. This test fetches the FiFi test results from the IQE framework into
Robottelo so Satellite QE's tooling (Report Portal, Polarion) can use it transparently


:Requirement: RemoteExecution

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: RemoteExecution

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
import requests

from robottelo.config import settings
from robottelo.decorators import skip_if_not_set


@skip_if_not_set('iqe')
@pytest.mark.tier2
def test_fifi():
    """Fetch FiFi test result from IQE's Jenkins

    :id: d63f87e5-66e6-488a-8c44-4129259494a6

    :expectedresults: There are some tests found and all of the passed
    """
    jenkins = settings.iqe.jenkins
    fifi_job = settings.iqe.fifi_job
    job = requests.get(f'{jenkins}/{fifi_job}/api/json').json()
    last_build_number = job['lastCompletedBuild']['number']
    all_tests = requests.get(
        f'{jenkins}/{fifi_job}/{last_build_number}/testReport/api/json'
    ).json()['suites'][0]['cases']
    tests = [
        test for test in all_tests if 'sat69' in test['name']
    ]  # select those with matching Satellite version
    test_count = len(tests)
    successful_test_count = sum(1 for test in tests if test['status'] == 'PASSED')
    assert test_count == successful_test_count
    assert test_count > 0
