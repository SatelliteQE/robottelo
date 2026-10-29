"""Test for Insights Cloud rule endpoint.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:team: Proton

:CaseImportance: High

"""
import pytest
from nailgun import client
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

    response.status_code == 404

def test_insights_rule_existing(module_org, module_target_sat):
    """Check that a known rule can be retrieved and has no acked hosts.

    :id: f9ffee5d-b633-4bcc-8b12-9d13af6ce604

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}
        2. Send GET request to /insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail

    :expectedresults: The rule is returned with correct rule_id and empty systems_detail.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    response.status_code == 200
    response.json()["rule_id"] == RULE_ID
    response.json()["hosts_acked_count"] == 0

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/rule/{RULE_ID}/systems_detail'
    
    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json() == []
    

@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_rule_reporting_rule(module_org, module_sca_manifest, module_target_sat, rhel_contenthost):
    """Check that a host reporting a known vulnerability appears in the rule systems_detail.

    :id: 0d0f5439-c375-4799-ae72-202f8fa6267d

    :steps:
        1. Upload a manifest to the organization
        2. Create an activation key and register a content host with insights
        3. Create an SSH config vulnerability on the host
        4. Run insights-client to upload data
        5. Verify the host reports are non-empty
        6. Verify the rule systems_detail shows the affected host

    :expectedresults: The host appears in the rule's systems_detail with count > 0.
    """
    module_target_sat.upload_manifest(module_org.id, module_sca_manifest.content)

    cvenv_id = module_target_sat.api_factory.get_cvenv_id(
        module_org.default_content_view, module_org.library
    )
    ak = module_target_sat.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=module_org,
    ).create()

    rhel_contenthost.register(
        module_org, None, ak.name, module_target_sat,
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