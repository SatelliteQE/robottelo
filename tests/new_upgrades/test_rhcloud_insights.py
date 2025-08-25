"""Tests for RH Cloud - Inventory

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

from datetime import UTC, datetime

from box import Box
from fauxfactory import gen_alpha
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


def sync_recommendations(satellite, org):
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_insights:sync'
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    result = satellite.execute(cmd)
    wait_for(
        lambda: satellite.api.ForemanTask()
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
    rhel_contenthost,
    function_sca_manifest,
):
    """Pre-upgrade scenario that creates local advisor Satellite with Insights clients.

    :id: preupgrade-8c2901a0-dad1-4e53-84e7-66aa09c68830

    :steps:
        1. Configure a Satellite with local advisor enabled.
        2. Register hosts with Satellite and Insights.
    :expectedresults: Content-view created with various repositories.
    """
    hosted_insights = getattr(request, 'param', True)
    target_sat = (
        request.getfixturevalue('hosted_insights_upgrade')
        if hosted_insights
        else request.getfixturevalue('local_insights_upgrade')
    )
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'org': None,
                'rhel_contenthost': rhel_contenthost,
                'activation_key': None,
            }
        )
        test_name = f'insights_upgrade_{gen_alpha()}'
        test_data.test_name = test_name
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        test_data.org = org
        if not hosted_insights:
            iop_settings = settings.rh_cloud.iop_advisor_engine
            target_sat.configure_insights_on_prem(
                iop_settings.username, iop_settings.token, iop_settings.registry
            )
        target_sat.upload_manifest(org.id, function_sca_manifest.content)
        activation_key = target_sat.api.ActivationKey(
            name=f'{test_name}_activation_key',
            content_view=org.default_content_view,
            organization=org,
            environment=target_sat.api.LifecycleEnvironment(id=org.library.id),
        ).create()
        test_data.activation_key = activation_key
        rhel_contenthost.add_rex_key(satellite=target_sat)
        rhel_contenthost.configure_insights_client(
            satellite=target_sat,
            activation_key=activation_key,
            org=org,
            rhel_distro=f"rhel{rhel_contenthost.os_version.major}",
        )
        iop_settings = settings.rh_cloud.iop_advisor_engine
        rhel_contenthost.create_insights_vulnerability()
        local_advisor_enabled = target_sat.api.RHCloud().advisor_engine_config()[
            'use_local_advisor_engine'
        ]
        # Verify insights-client can update to latest version available from server
        assert rhel_contenthost.execute('insights-client --version').status == 0
        # Prepare misconfigured machine and upload data to Insights
        rhel_contenthost.create_insights_vulnerability()
        if not local_advisor_enabled:
            sync_recommendations(target_sat, org)
        if local_advisor_enabled:
            target_sat.execute(
                f'wget -O {CUSTOM_HIERA_LOCATION} {iop_settings.SATELLITE_IOP_REPO[:-4]}/-/raw/main/playbooks/custom-hiera.yaml'
            )
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.local_insights_upgrades
@pytest.mark.hosted_insights_upgrades
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.parametrize("iop_upgrade_setup", [True, False], ids=["hosted", "local"], indirect=True)
def test_rhcloud_insights_upgrade(iop_upgrade_setup):
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
    target_sat = iop_upgrade_setup.target_sat
    rhel_contenthost = iop_upgrade_setup.rhel_contenthost
    org = iop_upgrade_setup.org
    REC_QUERY = f'hostname = "{rhel_contenthost.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'
    local_advisor_enabled = target_sat.local_advisor_enabled()
    assert local_advisor_enabled
    service_status = target_sat.cli.Service.status(options={'brief': True})
    assert 'FAIL' not in service_status.stdout
    assert service_status.status == 0
    service_list = target_sat.cli.Service.list()
    assert 'FAIL' not in service_list.stdout
    assert service_list.status == 0
    for service in (
        IOP_SERVICES + SATELLITE_SERVICES if local_advisor_enabled else SATELLITE_SERVICES
    ):
        assert service in service_list.stdout
    if local_advisor_enabled:
        assert rhel_contenthost.execute('insights-client --register').status == 0
    assert rhel_contenthost.execute('insights-client --test-connection').status == 0
    assert rhel_contenthost.execute('insights-client --status').status == 0
    with target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        # Verify that we can see the rule hit via insights-client
        diagnosis_result = rhel_contenthost.execute('insights-client --diagnosis')
        assert diagnosis_result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in diagnosis_result.stdout
        # Search for the recommendation.
        search_result = session.cloudinsights.search(REC_QUERY)[0]
        assert search_result['Hostname'] == rhel_contenthost.hostname
        assert search_result['Recommendation'] == OPENSSH_RECOMMENDATION
        # Run the remediation.
        session.cloudinsights.remediate(OPENSSH_RECOMMENDATION)
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Insights remediations for selected issues',
            host_name=rhel_contenthost.hostname,
        )
        # Re-sync the recommendations (hosted Insights only).
        if not local_advisor_enabled:
            sync_recommendations(target_sat, org)
        # Verify that the recommendation is not listed anymore.
        assert not session.cloudinsights.search(REC_QUERY)
