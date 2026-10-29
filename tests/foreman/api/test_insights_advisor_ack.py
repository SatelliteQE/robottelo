"""Test for Insights Cloud ack endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""

from nailgun import client

RULE_ID = "hardening_ssh_config_perms|OPENSSH_HARDENING_CONFIG_PERMS"


def test_insights_ack(module_org, module_target_sat):
    """Check that the ack endpoint returns empty results for an org with no acknowledgements.

    :id: 3907569a-c5a9-4186-8b4d-84473503f7f6

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/ack

    :expectedresults: The response returns 200 with count equal to 0 and empty data.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0
    assert response.json()["data"] == []


def test_insights_ack_not_existing(module_org, module_target_sat):
    """Check that requesting an ack for a non-existing rule returns 404.

    :id: 4ad25e6f-3e9c-4148-b3ce-56704bf445c0

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/ack/xxx

    :expectedresults: The response returns 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/xxx'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404


def test_insights_create_ack(module_org, module_target_sat):
    """Check full CRUD lifecycle of an ack: create, read, update, and delete.

    :id: 5e862132-6e53-4ed8-a7f5-2e2f7c476d8b

    :steps:
        1. Send POST request to /insights_cloud/api/insights/v1/ack/ with rule_id and justification
        2. Send GET request to /insights_cloud/api/insights/v1/ack to verify list count > 0
        3. Send GET request to /insights_cloud/api/insights/v1/ack/{RULE_ID} to verify creation
        4. Send PUT request to /insights_cloud/api/insights/v1/ack/{RULE_ID}/ with new justification
        5. Send GET request to /insights_cloud/api/insights/v1/ack/{RULE_ID} to verify update
        6. Send DELETE request to /insights_cloud/api/insights/v1/ack/{RULE_ID}/
        7. Send GET request to /insights_cloud/api/insights/v1/ack to verify list count == 0

    :expectedresults: The ack is created with 200, listed, readable with correct data, updated
        with new justification, deleted with 204, and the list reflects the lifecycle.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/'
    justification = 'first justification'

    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule_id': RULE_ID,
            'justification': justification,
        },
    )

    assert response.status_code == 200
    assert response.json()["rule"] == RULE_ID
    assert response.json()["justification"] == justification

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["rule"] == RULE_ID
    assert response.json()["justification"] == justification

    new_justification = "new justification"

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}/'
    response = client.put(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'justification': new_justification,
        },
    )

    assert response.status_code == 200
    assert response.json()["rule"] == RULE_ID
    assert response.json()["justification"] == new_justification

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["rule"] == RULE_ID
    assert response.json()["justification"] == new_justification

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}/'
    response = client.delete(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 204

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0


def test_insights_ack_delete_not_existing(module_org, module_target_sat):
    """Check that deleting a non-existing ack returns 404.

    :id: 1fc393ee-7139-4432-86ac-46c305e0203a

    :steps:
        1. Send DELETE request to /insights_cloud/api/insights/v1/ack/xxxx/
        2. Send DELETE request to /insights_cloud/api/insights/v1/ack/{RULE_ID}/

    :expectedresults: Both responses return 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/xxxx/'
    response = client.delete(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}/'
    response = client.delete(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404


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

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/'
    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
        data={
            'rule_id': RULE_ID,
            'justification': 'org isolation test',
        },
    )

    assert response.status_code == 200

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_b.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}/'
    response = client.delete(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': org_a.id},
    )

    assert response.status_code == 204
