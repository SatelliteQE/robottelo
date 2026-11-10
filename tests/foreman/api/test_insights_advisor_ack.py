"""Test for Insights ack endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""

from nailgun import client

from robottelo.constants import OPENSSH_RECOMMENDATION_RULE_ID


def test_insights_ack_multi_org_isolation(module_target_sat):
    """Check that acks created in one org are not visible in another org.

    :id: 5a696a05-360a-438f-90f1-d568f9ddb287

    :steps:
        1. Create two organizations
        2. Send POST to /insights_cloud/api/insights/v1/ack/ in org A
        3. Send GET to /insights_cloud/api/insights/v1/ack in org B
        4. Send GET to /insights_cloud/api/insights/v1/ack in org A
        5. Send DELETE to /insights_cloud/api/insights/v1/ack/{RULE_ID}/ in org A

    :expectedresults: Org B returns count == 0. Org A returns count > 0.
    """
    org_a = module_target_sat.api.Organization().create()
    org_b = module_target_sat.api.Organization().create()

    ack_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/'
    response = client.post(
        ack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
        data={
            'rule_id': OPENSSH_RECOMMENDATION_RULE_ID,
            'justification': 'org isolation test',
        },
    )

    assert response.status_code == 200

    response = client.get(
        ack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_b.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0

    response = client.get(
        ack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 1
    assert response.json()["data"][0]["rule"] == OPENSSH_RECOMMENDATION_RULE_ID

    ack_rule_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{OPENSSH_RECOMMENDATION_RULE_ID}/'
    response = client.delete(
        ack_rule_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
    )

    assert response.status_code == 204
