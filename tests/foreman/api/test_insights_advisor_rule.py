"""Test for Insights rule endpoint.

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
def module_insights_ak(module_org, module_sca_manifest, module_target_sat_insights):
    """Upload a manifest and create an activation key for insights tests."""
    module_target_sat_insights.upload_manifest(module_org.id, module_sca_manifest.content)
    cvenv_id = module_target_sat_insights.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    return module_target_sat_insights.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()


def test_insights_rule(module_org, module_target_sat_insights):
    """Check that the rule endpoint returns available rules.

    :id: c9f4fa60-678f-4e95-8236-7c59de04bcd3

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/

    :expectedresults: The response returns 200 with count greater than 0.
    """
    path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/'

    response = client.get(
        path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0
    assert "data" in response.json()
    assert len(response.json()["data"]) > 0
    assert "category" in response.json()["data"][0]
    assert "created_at" in response.json()["data"][0]
    assert "description" in response.json()["data"][0]
    assert "generic" in response.json()["data"][0]
    assert "hosts_acked_count" in response.json()["data"][0]
    assert "impact" in response.json()["data"][0]
    assert "impacted_systems_count" in response.json()["data"][0]
    assert "playbook_count" in response.json()["data"][0]
    assert "rating" in response.json()["data"][0]
    assert "reason" in response.json()["data"][0]
    assert "reports_shown" in response.json()["data"][0]
    assert "resolution_set" in response.json()["data"][0]
    assert "rule_id" in response.json()["data"][0]
    assert "rule_status" in response.json()["data"][0]
    assert "summary" in response.json()["data"][0]
    assert "tags" in response.json()["data"][0]
    assert "updated_at" in response.json()["data"][0]


def test_insights_rule_existing(module_org, module_target_sat_insights):
    """Check that a known rule can be retrieved and has no impacted systems.

    :id: f9ffee5d-b633-4bcc-8b12-9d13af6ce604

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}
        2. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail

    :expectedresults: The rule is returned with correct rule_id, zero hosts_acked_count,
        and systems_detail count equal to 0.
    """
    rule_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}'

    response = client.get(
        rule_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["rule_id"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["hosts_acked_count"] == 0

    systems_detail_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems_detail'

    response = client.get(
        systems_detail_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_rule_reporting_rule(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that a host reporting a known vulnerability appears in rule endpoints.

    :id: 0d0f5439-c375-4799-ae72-202f8fa6267d

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability on the host
        3. Run insights-client to upload data
        4. Verify the host has reports via system/{uuid}/reports
        5. Verify the rule systems_detail shows the affected host
        6. Verify the rule systems endpoint contains the host UUID

    :expectedresults: The host appears in reports, systems_detail, and systems endpoints.
    """
    rhel_contenthost.api_register(
        module_target_sat_insights,
        organization=module_org,
        activation_keys=[module_insights_ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')
    rhel_contenthost.execute('chmod 777 /etc/ssh/sshd_config')

    rhel_contenthost.execute('insights-client')

    insights_uuid = rhel_contenthost.get_insights_id()

    reports_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/system/{insights_uuid}/reports'

    def _check_reports():
        response = client.get(
            reports_path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        return len(response.json()) > 0

    wait_for(_check_reports, timeout=120, delay=10, handle_exception=True)

    systems_detail_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems_detail'

    response = client.get(
        systems_detail_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 1
    assert response.json()["data"][0]["system_uuid"] == insights_uuid

    systems_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems'

    response = client.get(
        systems_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuid in response.json()["host_ids"]


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_ack_hosts(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that hosts can be acked for a specific rule via the ack_hosts endpoint.

    :id: 7ce03f45-d8a0-40c5-98f9-4077b3451698

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability on the host
        3. Run insights-client to upload data
        4. Send POST request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/ack_hosts/
            with the host's insights UUID and justification
        5. Send GET request to /insights_cloud/api/insights/v1/hostack/

    :expectedresults: The ack_hosts POST returns 200 with count > 0 and empty host_ids.
    """
    rhel_contenthost.api_register(
        module_target_sat_insights,
        organization=module_org,
        activation_keys=[module_insights_ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')
    rhel_contenthost.execute('chmod 777 /etc/ssh/sshd_config')

    rhel_contenthost.execute('insights-client')

    insights_uuid = rhel_contenthost.get_insights_id()

    justification = 'first justification'

    ack_hosts_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/ack_hosts/'

    response = client.post(
        ack_hosts_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'systems': [insights_uuid],
            'justification': justification,
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] > 0
    assert response.json()["host_ids"] == []

    hostack_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.get(
        hostack_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 1
    assert response.json()["data"][0]["rule"] == OPENSSH_RECOMMENDATION_RULE_ID
    assert response.json()["data"][0]["system_uuid"] == insights_uuid
    assert response.json()["data"][0]["justification"] == justification


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_rule_ack_hides_all_hosts(
    module_org, module_insights_ak, module_target_sat_insights, content_hosts
):
    """Check that a rule-level ack hides all hosts from the rule systems endpoint.

    :id: 2dc0626b-0c3a-412b-8c01-be7694965d81

    :steps:
        1. Register two content hosts with insights
        2. Create the SSH config vulnerability on both hosts and run insights-client
        3. Wait for both hosts to appear in rule/{RULE_ID}/systems
        4. Send POST to /insights_cloud/api/insights/v1/ack/ to ack the rule
        5. Verify rule/{RULE_ID}/systems returns no host_ids
        6. Send DELETE to /insights_cloud/api/insights/v1/ack/{RULE_ID}/ to remove the ack
        7. Verify both hosts reappear in rule/{RULE_ID}/systems

    :expectedresults: A rule-level ack hides all hosts, not just one. After removing
        the ack, all hosts reappear.
    """
    insights_uuids = []
    for host in content_hosts:
        host.api_register(
            module_target_sat_insights,
            organization=module_org,
            activation_keys=[module_insights_ak.name],
            setup_insights=True,
        )
        host.execute('insights-client --register')
        host.execute('chmod 777 /etc/ssh/sshd_config')
        host.execute('insights-client')

        insights_uuids.append(host.get_insights_id())

    systems_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/rule/{OPENSSH_RECOMMENDATION_RULE_ID}/systems'

    def _check_both_hosts():
        response = client.get(
            systems_path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        assert "host_ids" in response.json()

        host_ids = response.json()["host_ids"]
        return insights_uuids[0] in host_ids and insights_uuids[1] in host_ids

    wait_for(_check_both_hosts, timeout=120, delay=10, handle_exception=True)

    ack_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/ack/'
    response = client.post(
        ack_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule_id': OPENSSH_RECOMMENDATION_RULE_ID,
            'justification': 'rule ack hides all hosts',
        },
    )

    assert response.status_code == 200

    response = client.get(
        systems_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuids[0] not in response.json()["host_ids"]
    assert insights_uuids[1] not in response.json()["host_ids"]

    ack_rule_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/ack/{OPENSSH_RECOMMENDATION_RULE_ID}/'
    response = client.delete(
        ack_rule_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 204

    response = client.get(
        systems_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuids[0] in response.json()["host_ids"]
    assert insights_uuids[1] in response.json()["host_ids"]
