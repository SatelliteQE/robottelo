"""Test for RH Cloud - IOP related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.constants import OPENSSH_RECOMMENDATION
from robottelo.utils.shared_resource import SharedResource
from tests.foreman.ui.test_rhcloud_insights import (
    create_insights_vulnerability as create_insights_recommendation,
)


@pytest.fixture
def iop_recommendations_upgrade_setup(
    iop_upgrade_shared_satellite,
    rhel_contenthost,
    upgrade_action,
):
    """Before upgrade, set up Satellite with IOP enabled and create conditions that
    generate advisor recommendations.

    :steps:
        1. Set up Satellite with IOP enabled.
        2. Create misconfigured machine to trigger advisor recommendations.
        3. Verify that recommendations appear on the Satellite.
        4. Save recommendation name, hostname, and organization for post-upgrade test.

    :expectedresults:
        1. IOP recommendations are visible in Satellite UI.
        2. Recommendation data is saved for post-upgrade validation.
    """
    target_sat = iop_upgrade_shared_satellite
    with SharedResource(
        target_sat.hostname, upgrade_action, target_sat=target_sat, action_is_recoverable=True
    ) as sat_upgrade:
        test_name = f'iop_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()

        # Verify insights-client package is installed
        assert rhel_contenthost.execute('insights-client --version').status == 0

        # Prepare misconfigured machine and upload data to Insights
        create_insights_recommendation(rhel_contenthost)

        with target_sat.ui_session() as session:
            session.organization.select(org_name=org.name)

            # Verify that we can see the rule hit via insights-client
            result = rhel_contenthost.execute('insights-client --diagnosis')
            assert result.status == 0
            assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

            # Search for the recommendation and verify it exists
            result = session.recommendationstab.search(OPENSSH_RECOMMENDATION)
            assert result[0]['Name'] == OPENSSH_RECOMMENDATION

        test_data = Box(
            {
                'recommendation_name': OPENSSH_RECOMMENDATION,
                'hostname': rhel_contenthost.hostname,
                'org_name': org.name,
                'org': org,
                'satellite': target_sat,
                'rhel_client': rhel_contenthost,
            }
        )
        sat_upgrade.ready()
        yield test_data


@pytest.mark.iop_upgrades
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
def test_iop_recommendations_upgrade(iop_recommendations_upgrade_setup):
    """After upgrade, verify IOP recommendations persist, can be searched,
    and remediation can be applied successfully.

    :id: 3d8a2f5f-ae74-444b-bf14-027c8ab33fca

    :steps:
        1. After Satellite upgrade, select the pre-upgrade organization.
        2. Navigate to Red Hat Lightspeed > Recommendations.
        3. Search for the pre-upgrade recommendation.
        4. Verify recommendation exists and can be found via search.
        5. Navigate to host details and verify recommendations are visible.
        6. Apply remediation from host details page.
        7. Verify remediation job completes successfully.

    :expectedresults:
        1. Pre-upgrade IOP recommendations are still visible post-upgrade.
        2. Search functionality works correctly.
        3. Host details page shows recommendations.
        4. Remediation can be applied successfully.
        5. Job invocation completes with success status.
    """
    recommendation_name = iop_recommendations_upgrade_setup.recommendation_name
    hostname = iop_recommendations_upgrade_setup.hostname
    org_name = iop_recommendations_upgrade_setup.org_name
    target_sat = iop_recommendations_upgrade_setup.satellite

    with target_sat.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Force register host with insights
        target_sat.execute('insights-client --register --force')

        # Search for the recommendation and verify it still exists post-upgrade
        result = session.recommendationstab.search(recommendation_name)
        assert result[0]['Name'] == recommendation_name

        # Get recommendations from host details page
        result = session.host_new.get_recommendations(hostname)
        assert any(row.get('Description') == recommendation_name for row in result), (
            f"No row found with Recommendation == {recommendation_name}"
        )

        # Apply remediation from host details page
        result = session.host_new.remediate_host_recommendation(
            hostname,
            recommendation_name,
        )

        # Verify that the job succeeded
        assert result['status']['Succeeded'] != 0
        assert result['overall_status']['is_success']

        # Verify that the recommendation is no longer listed after remediation
        result = session.host_new.get_recommendations(hostname)
        assert not any(row.get('Description') == recommendation_name for row in result), (
            f"Recommendation should not be present after remediation: {recommendation_name}"
        )
