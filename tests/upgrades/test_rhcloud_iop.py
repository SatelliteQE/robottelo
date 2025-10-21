"""Test for RH Cloud - IOP related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

import pytest

from robottelo.constants import OPENSSH_RECOMMENDATION
from tests.foreman.ui.test_rhcloud_insights import (
    create_insights_vulnerability as create_insights_recommendation,
)


class TestScenarioIOPRecommendations:
    """The scenario to test IOP recommendations functionality across satellite upgrade.

    Test Steps::

        1. Before Satellite upgrade, create a misconfigured host and generate IOP recommendations
        2. Save recommendation name, hostname, and organization for post-upgrade validation
        3. Upgrade Satellite
        4. Post-upgrade, verify recommendations persist and can be searched
        5. Apply remediation and verify job completion
    """

    @pytest.mark.pre_upgrade
    @pytest.mark.pit_server
    @pytest.mark.pit_client
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('N-1')
    @pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
    def test_pre_iop_recommendations_upgrade(
        self,
        rhel_insights_vm,
        rhcloud_manifest_org,
        module_target_sat_insights,
        save_test_data,
    ):
        """Before upgrade, set up Satellite with IOP enabled and create conditions that
        generate advisor recommendations.

        :id: 3d8a2f5f-ae74-444b-bf14-027c8ab33fca

        :steps:
            1. Set up Satellite with IOP enabled.
            2. Create misconfigured machine to trigger advisor recommendations.
            3. Verify that recommendations appear on the Satellite.
            4. Save recommendation name, hostname, and organization for post-upgrade test.

        :expectedresults:
            1. IOP recommendations are visible in Satellite UI.
            2. Recommendation data is saved for post-upgrade validation.
        """
        org_name = rhcloud_manifest_org.name

        # Verify insights-client package is installed
        assert rhel_insights_vm.execute('insights-client --version').status == 0

        # Prepare misconfigured machine and upload data to Insights
        create_insights_recommendation(rhel_insights_vm)

        with module_target_sat_insights.ui_session() as session:
            session.organization.select(org_name=org_name)

            # Verify that we can see the rule hit via insights-client
            result = rhel_insights_vm.execute('insights-client --diagnosis')
            assert result.status == 0
            assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

            # Search for the recommendation and verify it exists
            result = session.recommendationstab.search(OPENSSH_RECOMMENDATION)
            assert result[0]['Name'] == OPENSSH_RECOMMENDATION

            # Save data for post-upgrade test
            save_test_data(
                {
                    'recommendation_name': OPENSSH_RECOMMENDATION,
                    'hostname': rhel_insights_vm.hostname,
                    'org_name': org_name,
                }
            )

    @pytest.mark.post_upgrade(depend_on=test_pre_iop_recommendations_upgrade)
    def test_post_iop_recommendations_upgrade(
        self,
        module_target_sat_insights,
        pre_upgrade_data,
    ):
        """After upgrade, verify IOP recommendations persist, can be searched,
        and remediation can be applied successfully.

        :id: postupgrade-5a8e1a9b-9c6d-4f3a-b7c1-2d4e3f6a8b9c

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
        recommendation_name = pre_upgrade_data.recommendation_name
        hostname = pre_upgrade_data.hostname
        org_name = pre_upgrade_data.org_name

        with module_target_sat_insights.ui_session() as session:
            session.organization.select(org_name=org_name)

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
