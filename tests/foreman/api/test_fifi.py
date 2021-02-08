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


@pytest.mark.tier2
def test_fifi():
    """Fetch FiFi test result from IQE's Jenkins

    :id: d63f87e5-66e6-488a-8c44-4129259494a6

    :expectedresults: There are some tests found and all of the passed
    """
    job = requests.get(
        'https://insights-stg-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/view/'
        'FiFi/job/iqe-remediations-fifi-prod-basic/api/json'
    ).json()
    last_build_number = job['lastCompletedBuild']['number']
    all_tests = requests.get(
        f'https://insights-stg-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/view/FiFi/job/'
        f'iqe-remediations-fifi-prod-basic/{last_build_number}/testReport/api/json/'
    ).json()['suites'][0]['cases']
    tests = [
        test for test in all_tests if 'sat69' in test['name']
    ]  # select those with matching Satellite version
    test_count = len(tests)
    successful_test_count = sum(1 for test in tests if test['status'] == 'PASSED')
    assert test_count == successful_test_count
    assert test_count > 0
