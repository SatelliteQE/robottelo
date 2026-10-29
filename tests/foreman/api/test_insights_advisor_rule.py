"""Test for Insights Cloud rule endpoint.

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

RULE_ID = "hardening_ssh_config_perms|OPENSSH_HARDENING_CONFIG_PERMS"


def test_insights_rule(module_org, module_target_sat):
    """Check that the rule endpoint returns available rules.

    :id: c9f4fa60-678f-4e95-8236-7c59de04bcd3

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/

    :expectedresults: The response returns 200 with count greater than 0.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0


def test_insights_rule_not_existing(module_org, module_target_sat):
    """Check that requesting a non-existing rule returns 404.

    :id: 505357a7-b1a9-4c9d-80e3-f16ffce5ad83

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/xxx

    :expectedresults: The response returns 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/xxx'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404


def test_insights_rule_systems_detail_not_existing(module_org, module_target_sat):
    """Check that requesting systems_detail for a non-existing rule returns 404.

    :id: 9b1fd9d6-5bae-4c06-b353-cf36bab47395

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/xxx/systems_detail

    :expectedresults: The response returns 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/xxx/systems_detail'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404


def test_insights_rule_systems_not_existing(module_org, module_target_sat):
    """Check that requesting systems for a non-existing rule returns 404.

    :id: 9b7e9219-6228-4f59-b8d2-79af115b62e6

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/xxx/systems

    :expectedresults: The response returns 404.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/xxx/systems'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 404


def test_insights_rule_existing(module_org, module_target_sat):
    """Check that a known rule can be retrieved and has no impacted systems.

    :id: f9ffee5d-b633-4bcc-8b12-9d13af6ce604

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}
        2. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail

    :expectedresults: The rule is returned with correct rule_id, zero hosts_acked_count,
        and systems_detail count equal to 0.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["rule_id"] == RULE_ID
    assert response.json()["hosts_acked_count"] == 0

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_rule_reporting_rule(
    module_org, module_sca_manifest, module_target_sat, rhel_contenthost
):
    """Check that a host reporting a known vulnerability appears in rule endpoints.

    :id: 0d0f5439-c375-4799-ae72-202f8fa6267d

    :steps:
        1. Upload a manifest to the organization
        2. Create an activation key and register a content host with insights
        3. Create an SSH config vulnerability on the host
        4. Run insights-client to upload data
        5. Verify the host has reports via system/{uuid}/reports
        6. Verify the rule systems_detail shows the affected host
        7. Verify the rule systems endpoint contains the host UUID

    :expectedresults: The host appears in reports, systems_detail, and systems endpoints.
    """
    module_target_sat.upload_manifest(module_org.id, module_sca_manifest.content)

    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    ak = module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()

    rhel_contenthost.api_register(
        module_target_sat,
        organization=module_org,
        activation_keys=[ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')
    rhel_contenthost.execute('chmod 777 /etc/ssh/sshd_config')

    rhel_contenthost.execute('insights-client')

    result = rhel_contenthost.execute('cat /etc/insights-client/machine-id')
    insights_uuid = result.stdout.strip()

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/system/{insights_uuid}/reports'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert len(response.json()) > 0

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0
    assert response.json()["data"][0]["system_uuid"] == insights_uuid

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/systems'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuid in response.json()["host_ids"]


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_ack_hosts(module_org, module_sca_manifest, module_target_sat, rhel_contenthost):
    """Check that hosts can be acked for a specific rule via the ack_hosts endpoint.

    :id: 7ce03f45-d8a0-40c5-98f9-4077b3451698

    :steps:
        1. Upload a manifest to the organization
        2. Create an activation key and register a content host with insights
        3. Create an SSH config vulnerability on the host
        4. Run insights-client to upload data
        5. Send POST request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/ack_hosts/
            with the host's insights UUID and justification
        6. Send GET request to /insights_cloud/api/insights/v1/hostack/

    :expectedresults: The ack_hosts POST returns 200 with count > 0 and empty host_ids.
    """
    module_target_sat.upload_manifest(module_org.id, module_sca_manifest.content)

    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    ak = module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()

    rhel_contenthost.api_register(
        module_target_sat,
        organization=module_org,
        activation_keys=[ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')
    rhel_contenthost.execute('chmod 777 /etc/ssh/sshd_config')

    rhel_contenthost.execute('insights-client')

    result = rhel_contenthost.execute('cat /etc/insights-client/machine-id')
    insights_uuid = result.stdout.strip()

    justification = 'first justification'

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/ack_hosts/'

    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
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

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/hostack/'
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] > 0
    assert response.json()["data"][0]["rule"] == RULE_ID
    assert response.json()["data"][0]["system_uuid"] == insights_uuid
    assert response.json()["data"][0]["justification"] == justification


def test_insights_rule_ack_not_existing_host(module_org, module_target_sat):
    """Check that acking a non-existing host for a rule returns 400.

    :id: 7f0e02f5-72ac-4290-a7f4-365481a19ea6

    :steps:
        1. Send POST request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/ack_hosts/
            with a fake system UUID

    :expectedresults: The response returns 400.
    """

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/ack_hosts/'
    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'systems': ["f9ffee5d-b633-4bcc-8b12-9d13af6ce604"],
            'justification': "justification",
        },
    )

    assert response.status_code == 400


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_rule_ack_hides_all_hosts(
    module_org, module_sca_manifest, module_target_sat, content_hosts
):
    """Check that a rule-level ack hides all hosts from the rule systems endpoint.

    :id: 2dc0626b-0c3a-412b-8c01-be7694965d81

    :steps:
        1. Upload a manifest and register two content hosts with insights
        2. Create the SSH config vulnerability on both hosts and run insights-client
        3. Wait for both hosts to appear in rule/{RULE_ID}/systems
        4. Send POST to /insights_cloud/api/insights/v1/ack/ to ack the rule
        5. Verify rule/{RULE_ID}/systems returns no host_ids
        6. Send DELETE to /insights_cloud/api/insights/v1/ack/{RULE_ID}/ to remove the ack
        7. Verify both hosts reappear in rule/{RULE_ID}/systems

    :expectedresults: A rule-level ack hides all hosts, not just one. After removing
        the ack, all hosts reappear.
    """
    module_target_sat.upload_manifest(module_org.id, module_sca_manifest.content)

    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    ak = module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()

    insights_uuids = []
    for host in content_hosts:
        host.api_register(
            module_target_sat,
            organization=module_org,
            activation_keys=[ak.name],
            setup_insights=True,
        )
        host.execute('insights-client --register')
        host.execute('chmod 777 /etc/ssh/sshd_config')
        host.execute('insights-client')

        result = host.execute('cat /etc/insights-client/machine-id')
        insights_uuids.append(result.stdout.strip())

    systems_path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/systems'

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

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/'
    response = client.post(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule_id': RULE_ID,
            'justification': 'rule ack hides all hosts',
        },
    )

    assert response.status_code == 200

    response = client.get(
        systems_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuids[0] not in response.json()["host_ids"]
    assert insights_uuids[1] not in response.json()["host_ids"]

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/ack/{RULE_ID}/'
    response = client.delete(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 204

    response = client.get(
        systems_path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert insights_uuids[0] in response.json()["host_ids"]
    assert insights_uuids[1] in response.json()["host_ids"]
