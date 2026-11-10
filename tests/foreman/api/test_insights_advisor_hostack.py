"""Test for Insights hostack endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""

from nailgun import client
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import OPENSSH_RECOMMENDATION_RULE_ID


@pytest.fixture(scope='module')
def module_insights_ak(module_org, module_sca_manifest, module_target_sat):
    """Upload a manifest and create an activation key for insights tests."""
    module_target_sat.upload_manifest(module_org.id, module_sca_manifest.content)
    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    return module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_create_hostack_not_existing_rule(
    module_org, module_insights_ak, module_target_sat, rhel_contenthost
):
    """Check that creating a hostack with a non-existing rule returns 400.

    :id: acdee8d1-90c0-499e-baab-705e14412bde

    :steps:
        1. Register a content host with insights
        2. Run insights-client --register on the content host
        3. Send POST to /insights_cloud/api/insights/v1/hostack/ with a fake rule

    :expectedresults: The response returns 400.
    """
    rhel_contenthost.api_register(
        module_target_sat,
        organization=module_org,
        activation_keys=[module_insights_ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')

    insights_uuid = rhel_contenthost.get_insights_id()

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule': 'xxx',
            'system_uuid': insights_uuid,
            'justification': 'justification',
        },
    )

    assert response.status_code == 400


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_create_hostack(
    module_org, module_insights_ak, module_target_sat, rhel_contenthost
):
    """Check full CRUD lifecycle of a hostack: create, list, read, update, and delete.

    :id: 3ecfefa3-69e6-4d0b-a3fe-ba3a707b2c51

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability and run insights-client
        3. Wait for the host to appear in rule/{RULE_ID}/systems
        4. Send POST to /insights_cloud/api/insights/v1/hostack/ to create a hostack
        5. Send GET to /insights_cloud/api/insights/v1/hostack/ to list hostacks
        6. Verify the host is no longer in rule/{RULE_ID}/systems (acked)
        7. Verify rule/{RULE_ID} shows hosts_acked_count > 0
        8. Send GET to /insights_cloud/api/insights/v1/hostack/{id}/ to read the hostack
        9. Send PUT to /insights_cloud/api/insights/v1/hostack/{id}/ to update justification
        10. Send GET to verify updated justification
        11. Send DELETE to /insights_cloud/api/insights/v1/hostack/{id}/
        12. Verify rule/{RULE_ID} shows hosts_acked_count == 0
        13. Verify the host reappears in rule/{RULE_ID}/systems

    :expectedresults: The hostack is created, listed, read, updated, and deleted successfully.
        The acked host is removed from the rule systems list, hosts_acked_count reflects
        the hostack lifecycle, and the host reappears after deletion.
    """
    rhel_contenthost.api_register(
        module_target_sat,
        organization=module_org,
        activation_keys=[module_insights_ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')
    rhel_contenthost.execute('chmod 777 /etc/ssh/sshd_config')

    rhel_contenthost.execute('insights-client')

    insights_uuid = rhel_contenthost.get_insights_id()

    systems_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems'
    hostack_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    rule_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}'

    def _check_systems():
        response = client.get(
            systems_path,
            auth=module_target_sat.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        return insights_uuid in response.json()["host_ids"]

    wait_for(_check_systems, timeout=120, delay=10, handle_exception=True)

    justification = 'first justification'

    response = client.post(
        hostack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule': OPENSSH_RECOMMENDATION_RULE_ID,
            'system_uuid': insights_uuid,
            'justification': justification,
        },
    )

    assert response.status_code == 200
    assert response.json()["rule"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["system_uuid"] == insights_uuid
    assert response.json()["justification"] == justification

    hostack_id = response.json()["id"]
    hostack_item_path = (
        f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/{hostack_id}/'
    )

    response = client.get(
        hostack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 1
    assert response.json()["data"][0]["id"] == hostack_id
    assert response.json()["data"][0]["rule"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["data"][0]["justification"] == justification

    response = client.get(
        systems_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuid not in response.json()["host_ids"]

    response = client.get(
        rule_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["hosts_acked_count"] > 0

    response = client.get(
        hostack_item_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == hostack_id
    assert response.json()["rule"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["justification"] == justification

    new_justification = "new justification"

    response = client.put(
        hostack_item_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'justification': new_justification,
        },
    )

    assert response.status_code == 200
    assert response.json()["justification"] == new_justification

    response = client.get(
        hostack_item_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == hostack_id
    assert response.json()["rule"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["justification"] == new_justification

    response = client.delete(
        hostack_item_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 204

    response = client.get(
        rule_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["hosts_acked_count"] == 0

    response = client.get(
        systems_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuid in response.json()["host_ids"]


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_hostack_multi_host(
    module_org, module_insights_ak, module_target_sat, content_hosts
):
    """Check that acking one host does not affect another host reporting the same rule.

    :id: dca5020d-e757-4fce-91e4-4a60df909bbe

    :steps:
        1. Register two content hosts with insights
        2. Create the SSH config vulnerability on both hosts and run insights-client
        3. Wait for both hosts to appear in rule/{RULE_ID}/systems
        4. Create a hostack for host A only
        5. Verify host A is removed from rule/{RULE_ID}/systems
        6. Verify host B remains in rule/{RULE_ID}/systems
        7. Verify hosts_acked_count == 1
        8. Delete the hostack

    :expectedresults: Only the acked host is removed from the rule systems list.
        The other host remains unaffected.
    """
    insights_uuids = []
    for host in content_hosts:
        host.api_register(
            module_target_sat,
            organization=module_org,
            activation_keys=[module_insights_ak.name],
            setup_insights=True,
        )
        host.execute('insights-client --register')
        host.execute('chmod 777 /etc/ssh/sshd_config')
        host.execute('insights-client')

        insights_uuids.append(host.get_insights_id())

    systems_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems'

    def _check_both_hosts():
        response = client.get(
            systems_path,
            auth=module_target_sat.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        host_ids = response.json()["host_ids"]
        return insights_uuids[0] in host_ids and insights_uuids[1] in host_ids

    wait_for(_check_both_hosts, timeout=120, delay=10, handle_exception=True)

    hostack_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.post(
        hostack_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule': OPENSSH_RECOMMENDATION_RULE_ID,
            'system_uuid': insights_uuids[0],
            'justification': 'multi-host test',
        },
    )

    assert response.status_code == 200
    hostack_id = response.json()["id"]

    response = client.get(
        systems_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuids[0] not in response.json()["host_ids"]
    assert insights_uuids[1] in response.json()["host_ids"]

    rule_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}'
    response = client.get(
        rule_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["hosts_acked_count"] == 1

    hostack_item_path = (
        f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/{hostack_id}/'
    )
    response = client.delete(
        hostack_item_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 204
