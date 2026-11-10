"""Test for Insights stats overview endpoint.

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
def test_insights_stats_overview_one_system(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that stats overview reflects one important recommendation after a host reports a vulnerability.

    :id: d2d8e5bc-2d9b-4ad9-9e06-9039d75d07cd

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability on the host
        3. Run insights-client to upload data
        4. Send GET request to /insights_cloud/api/insights/v1/stats/overview

    :expectedresults: The response returns 200 with important equal to 1.
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

    path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/stats/overview'

    def _check_systems():
        response = client.get(
            path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        assert response.json()['pathways'] == 0
        assert response.json()['incidents'] == 0
        assert response.json()['critical'] == 0

        return response.json()['important'] == 1

    wait_for(_check_systems, timeout=120, delay=10, handle_exception=True)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(f'^{settings.content_host.default_rhel_version}$')
def test_insights_stats_overview_after_ack(
    module_org, module_insights_ak, module_target_sat_insights, rhel_contenthost
):
    """Check that stats overview reflects zero important after acking the rule.

    :id: 5bd5c862-0d56-4198-8252-8fbe13deb380

    :steps:
        1. Register a content host with insights
        2. Create an SSH config vulnerability and run insights-client
        3. Poll stats/overview until important == 1
        4. Send POST to /insights_cloud/api/insights/v1/ack/ to ack the rule
        5. Send GET to /insights_cloud/api/insights/v1/stats/overview
        6. Send DELETE to /insights_cloud/api/insights/v1/ack/{RULE_ID}/ to remove the ack
        7. Send GET to /insights_cloud/api/insights/v1/stats/overview

    :expectedresults: After acking, important drops to 0. After removing the ack,
        important returns to 1.
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

    overview_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/stats/overview'

    def _check_important():
        response = client.get(
            overview_path,
            auth=module_target_sat_insights.nailgun_cfg.auth,
            verify=False,
            headers={'Accept': 'application/json'},
            params={'organization_id': module_org.id},
        )
        assert response.status_code == 200
        return response.json()['important'] == 1

    wait_for(_check_important, timeout=120, delay=10, handle_exception=True)

    ack_path = f'{module_target_sat_insights.url}/insights_cloud/api/insights/v1/ack/'
    response = client.post(
        ack_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
        data={
            'rule_id': OPENSSH_RECOMMENDATION_RULE_ID,
            'justification': 'ack for overview test',
        },
    )

    assert response.status_code == 200

    response = client.get(
        overview_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()['important'] == 0

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
        overview_path,
        auth=module_target_sat_insights.nailgun_cfg.auth,
        verify=False,
        headers={'Accept': 'application/json'},
        params={'organization_id': module_org.id},
    )

    assert response.status_code == 200
    assert response.json()['important'] == 1
