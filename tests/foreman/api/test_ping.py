"""Test Class for api ping

:Requirement: Ping

:CaseAutomation: Automated

:CaseComponent: API

:Team: Endeavour

:CaseImportance: Critical

"""

import pytest


@pytest.mark.e2e
@pytest.mark.build_sanity
@pytest.mark.upgrade
def test_positive_ping(target_sat):
    """Check if all services are running

    :id: b8ecc7ba-8007-4067-bf99-21a82c833de7

    :expectedresults: Overall and individual Katello services status should be 'ok'.
    """
    response = target_sat.api.Ping().search_json()
    # Full response format:
    #
    # {'results': {
    #     'foreman': {'cache': {'servers': [{'duration_ms': '0', 'status': 'ok'}]},
    #                 'database': {'active': True, 'duration_ms': '0'}},
    #     'foreman_rh_cloud': {'services': {
    #         'advisor': {'duration_ms': '27', 'status': 'ok'},
    #         'vulnerability': {'duration_ms': '26', 'status': 'ok'},
    #     }, 'status': 'ok'},
    #     'katello': {'services': {
    #         'candlepin': {'duration_ms': '16', 'status': 'ok'},
    #         'candlepin_auth': {'duration_ms': '15', 'status': 'ok'},
    #         'candlepin_events': {'duration_ms': '0', 'message': '9 Processed, 0 Failed', 'status': 'ok'},
    #         'foreman_tasks': {'duration_ms': '2', 'status': 'ok'},
    #         'katello_events': {'duration_ms': '1', 'message': '3 Processed, 0 Failed', 'status': 'ok'},
    #         'pulp3': {'duration_ms': '97', 'status': 'ok'},
    #         'pulp3_content': {'duration_ms': '47', 'status': 'ok'},
    #     }, 'status': 'ok'}
    # }}
    katello = response['results']['katello']
    assert katello['status'] == 'ok'  # overall status
    services = katello['services']
    assert all(service['status'] == 'ok' for service in services.values()), (
        'Not all services seem to be up and running!'
    )
