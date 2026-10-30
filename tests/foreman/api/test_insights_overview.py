"""Test for Insights Cloud stats overview endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""

from nailgun import client


def test_insights_stats_overview(module_org, module_target_sat):
    """Check that the stats overview endpoint returns zero counts for an empty org.

    :id: 3362a264-287f-4492-ab98-6719cc7958df

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/stats/overview

    :expectedresults: The response returns 200 with pathways, incidents, critical,
        and important equal to 0.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/stats/overview'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )
    assert response.status_code == 200

    assert response.json()['pathways'] == 0
    assert response.json()['incidents'] == 0
    assert response.json()['critical'] == 0
    assert response.json()['important'] == 0
