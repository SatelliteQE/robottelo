"""Test for Insights Cloud stats overview endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""

from nailgun import client

RULE_ID = 'network_ipv6_dev_route_crash|NETWORK_IPV6_DEV_ROUTE_CRASH'
SYSTEM_UUID = 'REPLACE_WITH_REAL_INVENTORY_UUID'


def test_insights_empty_hostacks(module_org, module_target_sat):
    """Check that the hostack endpoint returns empty results for an org with no hostacks.

    :id: 3a7f2efc-b37b-4afe-aa47-643739243a16

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/hostack/

    :expectedresults: The response returns 200 with count equal to 0 and empty data.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()['meta']['count'] == 0
    assert response.json()['data'] == []

def test_insights_not_existing_hostack(module_org, module_target_sat):
    """Check that requesting a non-existing hostack returns 404.

    :id: 86d623c5-512b-4f4f-b06a-bb7d8bfd04ed

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/hostack/1

    :expectedresults: The response returns 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/1'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404

def test_insights_create_hostack(module_org, module_target_sat):
    """Check that a hostack can be created via POST request.

    :id: 1a1b8d2a-7719-4674-b0d3-9e405778e85e

    :steps:
        1. Send POST request to /insights_cloud/api/insights/v1/hostack/
            with rule, system_uuid, and justification

    :expectedresults: The hostack is created successfully.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.post(
            path,
            auth=module_target_sat.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
            data={
                'rule': RULE_ID,
                'system_uuid': SYSTEM_UUID,
                'justification': 'Robottelo hostack coverage',
            },
        )

   # print(response.status_code)
   # print(response.content)