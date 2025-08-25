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


def sync_recommendations(session):
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    session.cloudinsights.sync_hits()
    wait_for(
        lambda: session.task.search(f'Insights full sync and started_at >= "{timestamp}"'),
        timeout=180,
        delay=15,
        handle_exception=True,
    )


@pytest.fixture
def iop_upgrade_setup(
    request,
    module_target_sat_insights,
    upgrade_action,
    rhel_insights_vm,
    rhcloud_manifest_org,
):
    """Pre-upgrade scenario that creates local advisor Satellite with Insights clients.

    :id: preupgrade-8c2901a0-dad1-4e53-84e7-66aa09c68830

    :steps:
        1. Configure a Satellite with local advisor enabled.
        2. Register hosts with Satellite and Insights.
    :expectedresults: Content-view created with various repositories.
    """
    satellite = module_target_sat_insights
    iop_settings = settings.rh_cloud.iop_advisor_engine
    rhel_insights_vm.create_insights_vulnerability()
    org_name = rhcloud_manifest_org.name
    local_advisor_enabled = satellite.api.RHCloud().advisor_engine_config()[
        'use_local_advisor_engine'
    ]
    # Query for searching the available recommendation
    REC_QUERY = f'hostname = "{rhel_insights_vm.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'
    # Verify insights-client can update to latest version available from server
    assert rhel_insights_vm.execute('insights-client --version').status == 0
    # Prepare misconfigured machine and upload data to Insights
    rhel_insights_vm.create_insights_vulnerability()
    with satellite.ui_session() as session:
        session.organization.select(org_name=org_name)
        # Sync the recommendations (hosted Insights only).
        if not local_advisor_enabled:
            sync_recommendations(session)
        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout
        # Search for the recommendation.
        result = session.cloudinsights.search(REC_QUERY)[0]
        assert result['Hostname'] == rhel_insights_vm.hostname
        assert result['Recommendation'] == OPENSSH_RECOMMENDATION
    if local_advisor_enabled:
        satellite.execute(
            f'wget -O {CUSTOM_HIERA_LOCATION} {iop_settings.SATELLITE_IOP_REPO[:-4]}/-/raw/main/playbooks/custom-hiera.yaml'
        )
    with SharedResource(satellite.hostname, upgrade_action, target_sat=satellite) as sat_upgrade:
        test_data = Box(
            {
                'satellite': satellite,
                'org': rhcloud_manifest_org,
                'rhel_insights_vm': rhel_insights_vm,
                'REC_QUERY': REC_QUERY,
            }
        )
        sat_upgrade.ready()
        satellite._session = None
        yield test_data


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.parametrize(
    "module_target_sat_insights", [True, False], ids=["hosted", "local"], indirect=True
)
def test_rhcloud_insights_upgrade(request, iop_upgrade_setup, module_target_sat_insights):
    """Verify Satellite upgrade for hosted and local advisor with Insights client.

    :id: fce16a0a-da24-47fa-9df1-e94c1f4642a7

    :steps:
        1. Have Satellite with local or hosted Insights advisor enabled.
        2. Prepare misconfigured machine and upload its data to Insights.
        3. In Satellite UI, go to Insights > Recommendations.
        4. Verify recommendation related to "OpenSSH config permissions" issue is listed
        5. Perform Satellite upgrade.
        6. After Satellite upgrade, verify recommendation is still listed.

    :expectedresults:
        1. Insights recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Satellite upgrade completed successfully.
        3. Recommendation is listed on upgraded Satellite UI.
        4. IoP services are running.

    :CaseImportance: Critical

    :parametrized: yes

    :CaseAutomation: Automated
    """
    satellite = module_target_sat_insights.satellite
    rhel_insights_vm = module_target_sat_insights.rhel_insights_vm
    org = module_target_sat_insights.org
    assert satellite.api.RHCloud().advisor_engine_config()
    result = satellite.cli.Service.status(options={'brief': True})
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    for service in IOP_SERVICES + SATELLITE_SERVICES:
        assert service in result.stdout
    assert rhel_insights_vm.execute('insights-client --register').status == 0
    with satellite.ui_session() as session:
        session.organization.select(org_name=org.name)
        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout
        # Search for the recommendation.
        result = session.cloudinsights.search(satellite.REC_QUERY)[0]
        assert result['Hostname'] == rhel_insights_vm.hostname
        assert result['Recommendation'] == OPENSSH_RECOMMENDATION
