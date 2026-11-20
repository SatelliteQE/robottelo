"""Test for Insights system endpoint.

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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_systems(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that a registered host with insights appears in the systems endpoint.

    :id: 8afdc95b-4891-4d0b-b71a-66146ddc31cf

    :steps:
        1. Register a content host to Satellite with setup_insights enabled
        2. Run insights-client --register on the content host
        3. Poll GET /insights_cloud/api/insights/v1/system until count > 0

    :expectedresults: The registered host appears in the Insights systems endpoint.
    """
    rhel_contenthost.api_register(
        module_target_sat_insights,
        organization=module_org,
        activation_keys=[module_insights_ak.name],
        setup_insights=True,
    )

    rhel_contenthost.execute('insights-client --register')

    insights_uuid = rhel_contenthost.get_insights_id()

    path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/system'

    def _check_systems():
        response = client.get(
            path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        return (
            response.json()['meta']['count'] > 0
            and response.json()['data'][0]['system_uuid'] == insights_uuid
        )

    wait_for(_check_systems, timeout=120, delay=10, handle_exception=True)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_system_existing_with_rule(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that reports appear for a host with a known vulnerability.

    :id: baa4c870-a832-4778-897a-5f10f7ae32f5

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability on the host
        3. Run insights-client to upload data
        4. Poll GET /insights_cloud/api/insights/v1/system/{uuid}/reports until non-empty

    :expectedresults: The reports endpoint returns a non-empty list for the host.
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

    path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/system/{insights_uuid}/reports'

    def _check_systems():
        response = client.get(
            path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        return response.json() != [] and OPENSSH_RECOMMENDATION_RULE_ID in str(response.content)

    wait_for(_check_systems, timeout=120, delay=10, handle_exception=True)
