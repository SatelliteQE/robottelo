"""Tests for RH Cloud - Inventory

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

from datetime import UTC, datetime

from box import Box
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    CUSTOM_HIERA_LOCATION,
    IOP_SERVICES,
    OPENSSH_RECOMMENDATION,
    SATELLITE_SERVICES,
)
from robottelo.utils.shared_resource import SharedResource


def sync_recommendations(target_sat, org):
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_insights:sync'
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    result = target_sat.execute(cmd)
    wait_for(
        lambda: target_sat.api.ForemanTask()
        .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    assert result.status == 0
    assert 'Synchronized Insights hosts hits data' in result.stdout


@pytest.fixture
def iop_upgrade_setup(
    request,
    upgrade_action,
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Configure hosted/local advisor Satellite and register content host with insights client."""
    target_sat = module_target_sat_insights
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'org': rhcloud_manifest_org,
                'rhel_insights_vm': rhel_insights_vm,
            }
        )
        org = rhcloud_manifest_org
        local_advisor_enabled = target_sat.local_advisor_enabled
        # Verify insights-client can update to latest version available from server
        assert rhel_insights_vm.execute('insights-client --version').status == 0
        # Prepare misconfigured machine and upload data to Insights
        rhel_insights_vm.create_insights_vulnerability()
        if local_advisor_enabled:
            target_sat.execute(
                f'wget -O {CUSTOM_HIERA_LOCATION} {settings.rh_cloud.iop_advisor_engine.satellite_iop_repo[:-4]}/-/raw/main/playbooks/custom-hiera.yaml'
            )
            # Login to stage registry till 6.18 is GA
            if 6.18 in settings.robottelo.sat_non_ga_versions:
                iop_settings = settings.rh_cloud.iop_advisor_engine
                target_sat.podman_login(
                    iop_settings.stage_username,
                    iop_settings.stage_token,
                    iop_settings.stage_registry,
                )
        else:
            sync_recommendations(target_sat, org)
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.local_insights_upgrades
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.parametrize("module_target_sat_insights", [False], ids=["local"], indirect=True)
def test_rhcloud_insights_upgrade(request, iop_upgrade_setup, module_target_sat_insights):
    """Verify Satellite upgrade for hosted and local advisor with Insights client.
    Note: Currently, this test is parametrized to run for local advisor only.

    :id: fce16a0a-da24-47fa-9df1-e94c1f4642a7

    :steps:
        1. Have Satellite with local or hosted Insights advisor enabled.
        2. Prepare misconfigured machine and upload its data to Insights.
        3. In Satellite UI, go to Insights > Recommendations.
        4. Verify recommendation related to "OpenSSH config permissions" issue is listed
        5. Perform Satellite upgrade.
        6. After Satellite upgrade, verify recommendation is still listed.
        7. Run remediation for "OpenSSH config permissions" recommendation against host.
        8. Verify that the remediation job completed successfully.
        9. Refresh Insights recommendations (re-sync if using hosted Insights).
        10. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Satellite upgrade completed successfully
        3. IoP services are running.
        4. Recommendation is listed on upgraded Satellite UI.
        5. Remediation job finished successfully.
        6. Insights recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :parametrized: yes

    :CaseAutomation: Automated
    """
    target_sat = iop_upgrade_setup.target_sat
    rhel_insights_vm = iop_upgrade_setup.rhel_insights_vm
    org = iop_upgrade_setup.org
    REC_QUERY = f'hostname = "{rhel_insights_vm.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'
    local_insights = 'local' in request.node.name
    local_advisor_enabled = target_sat.local_advisor_enabled
    service_status = target_sat.cli.Service.status(options={'brief': True})
    assert 'FAIL' not in service_status.stdout
    assert service_status.status == 0
    service_list = target_sat.cli.Service.list()
    assert 'FAIL' not in service_list.stdout
    assert service_list.status == 0
    for service in IOP_SERVICES + SATELLITE_SERVICES if local_insights else SATELLITE_SERVICES:
        assert service in service_list.stdout
    if local_insights:
        assert local_advisor_enabled
        assert rhel_insights_vm.execute('insights-client --unregister --force').status == 0
        assert rhel_insights_vm.execute('insights-client --register').status == 0
    assert rhel_insights_vm.execute('insights-client --test-connection').status == 0
    assert rhel_insights_vm.execute('insights-client --status').status == 0
    # Verify that we can see the rule hit via insights-client
    diagnosis_result = rhel_insights_vm.execute('insights-client --diagnosis')
    assert diagnosis_result.status == 0
    assert 'OPENSSH_HARDENING_CONFIG_PERMS' in diagnosis_result.stdout
    with target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        # Search for the recommendation.
        search_result = session.cloudinsights.search(REC_QUERY)[0]
        assert search_result['Hostname'] == rhel_insights_vm.hostname
        assert search_result['Recommendation'] == OPENSSH_RECOMMENDATION
        # Run the remediation.
        session.cloudinsights.remediate(OPENSSH_RECOMMENDATION)
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Insights remediations for selected issues',
            host_name=rhel_insights_vm.hostname,
        )
        # Re-sync the recommendations (hosted Insights only).
        if not local_insights:
            sync_recommendations(target_sat, org)
        # Verify that the recommendation is not listed anymore.
        assert not session.cloudinsights.search(REC_QUERY)
