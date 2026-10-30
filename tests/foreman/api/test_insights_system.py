"""Test for Insights Cloud system endpoint.

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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_systems(module_org, module_sca_manifest, module_target_sat, rhel_contenthost):
    """Check that a registered host with insights appears in the systems endpoint.

    :id: 8afdc95b-4891-4d0b-b71a-66146ddc31cf

    :steps:
        1. Upload a manifest to the organization
        2. Create an activation key
        3. Register a content host to Satellite with setup_insights enabled
        4. Run insights-client --register on the content host
        5. Poll GET /insights_cloud/api/insights/v1/system until count > 0

    :expectedresults: The registered host appears in the Insights systems endpoint.
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

    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/system'

    def _check_systems():
        response = client.get(
            path,
            auth=module_target_sat.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        return response.json()['meta']['count'] > 0

    wait_for(_check_systems, timeout=120, delay=10, handle_exception=True)


def test_insights_systems_empty(module_org, module_target_sat):
    """Check that the systems endpoint returns empty results for an org with no insights hosts.

    :id: f66c1a19-9970-4b67-adee-6b23270a76ee

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/system for an empty org

    :expectedresults: The response returns 200 with count equal to 0.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/system'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()['meta']['count'] == 0

def test_insights_system_not_existing(module_org, module_target_sat):
    """Check that requesting reports for a non-existing system UUID returns empty list.

    :id: 9168fb40-b761-4942-b211-81878dbf9be9

    :steps:
        1. Send GET request to /insights_cloud/api/insights/v1/system/{fake_uuid}/reports

    :expectedresults: The response returns 200 with an empty list.
    """
    path = f'{module_target_sat.url}/insights_cloud/api/insights/v1/system/f66c1a19-9970-4b67-adee-6b23270a76ee/reports'

    response = client.get(
        path,
        auth=module_target_sat.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.json() == []
    assert response.status_code == 200

@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_system_existing(module_org, module_sca_manifest, module_target_sat, rhel_contenthost):
    """Check that reports for a registered insights host can be retrieved by its UUID.

    :id: 760cad28-3858-4a59-b4af-5bcb3fe15bda

    :steps:
        1. Upload a manifest to the organization
        2. Create an activation key and register a content host with insights
        3. Run insights-client --register on the content host
        4. Get the insights machine-id from the host
        5. Send GET request to /insights_cloud/api/insights/v1/system/{uuid}/reports

    :expectedresults: The response returns 200 with an empty reports list.
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

    assert response.status_code == 200
    assert response.json() == []