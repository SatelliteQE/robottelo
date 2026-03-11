"""Tests for RH Cloud - Inventory

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

from datetime import UTC, datetime

import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import DNF_RECOMMENDATION, OPENSSH_RECOMMENDATION


def create_insights_vulnerability(host):
    """Function to create vulnerabilities that can be remediated."""

    # Add vulnerability for DNF_RECOMMENDATION (RHEL 8+)
    if host.os_version.major > 7:
        host.run('dnf update -y dnf;sed -i -e "/^best/d" /etc/dnf/dnf.conf')

    # Add vulnerability for SSH_RECOMMENDATION
    host.run('chmod 777 /etc/ssh/sshd_config')

    # Upload insights data to Satellite
    result = host.run('insights-client')
    assert result.status == 0


def sync_recommendations(session):
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    session.cloudinsights.sync_hits()
    wait_for(
        lambda: session.task.search(f'Insights full sync and started_at >= "{timestamp}"'),
        timeout=180,
        delay=15,
        handle_exception=True,
    )


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
def test_rhcloud_insights_e2e(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Synchronize hits data from hosted, verify results are displayed in Satellite, and run remediation.

    :id: d952e83c-3faf-4299-a048-2eb6ccb8c9c2

    :steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. In Satellite UI, go to Insights > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against host.
        4. Verify that the remediation job completed successfully.
        5. Re-sync recommendations.
        6. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Remediation job finished successfully.
        3. Insights recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :BZ: 1965901, 1962048, 1976754

    :Verifies: SAT-36449

    :customerscenario: true

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Query for searching the available recommendation
    REC_QUERY = f'hostname = "{rhel_insights_vm.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'

    # Verify insights-client can update to latest version available from server
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_vulnerability(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Sync the recommendations
        sync_recommendations(session)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

        # Verify that errors are not present in production.log (SAT-36449)
        result = module_target_sat_insights.execute(
            'grep "500 Internal Server Error" /var/log/foreman/production.log'
        )
        assert result.status != 0
        result = module_target_sat_insights.execute(
            'grep "uninitialized constant" /var/log/foreman/production.log'
        )
        assert result.status != 0

        # Search for the recommendation.
        result = session.cloudinsights.search(REC_QUERY)[0]
        assert result['Hostname'] == rhel_insights_vm.hostname
        assert result['Recommendation'] == OPENSSH_RECOMMENDATION

        # Run the remediation.
        session.cloudinsights.remediate(OPENSSH_RECOMMENDATION)
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Insights remediations for selected issues',
            host_name=rhel_insights_vm.hostname,
        )

        # Re-sync the recommendations
        sync_recommendations(session)

        # Verify that the recommendation is not listed anymore.
        assert not session.cloudinsights.search(REC_QUERY)


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([10])
def test_rhcloud_insights_remediate_multiple_hosts(
    rhel_insights_vms,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Get rule hits data for multiple Hosts from hosted Insights Advisor, verify results are displayed in Satellite, and run remediations for all Hosts simultaneously.

    :id: 33463576-ccc0-4200-a5c0-6e7ffc9a03f7

    :steps:
        1. Prepare misconfigured machines and upload data to hosted or local Insights Advisor.
        2. In Satellite UI, go to Insights > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against Hosts.
        4. Verify that the remediation jobs completed successfully.
        5. Refresh the Insights recommendations.
        6. Search for previously remediated issues.
    :expectedresults:
        1. Insights recommendations related to "OpenSSH config permissions" issue are listed
            for misconfigured machines.
        2. Remediation jobs finished successfully.
        3. Insights recommendations related to "OpenSSH config permissions" issue are not listed.

    :CaseImportance: Critical

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name
    hostnames = [host.hostname for host in rhel_insights_vms]

    # Query for searching the available recommendations
    REC_QUERY = f'hostname ^ ({",".join(hostnames)}) and title = "{OPENSSH_RECOMMENDATION}"'

    # Query for searching the scheduled remediation tasks
    TASK_QUERY = (
        f'Remote action: Insights remediations for selected issues on ({"|".join(hostnames)})'
    )

    # Prepare the misconfigured hosts and upload Insights data
    for vm in rhel_insights_vms:
        create_insights_vulnerability(vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Sync the recommendations
        sync_recommendations(session)

        # Search for the recommendations
        results = session.cloudinsights.search(REC_QUERY)

        assert len(results) == len(rhel_insights_vms)
        assert all(result['Hostname'] in hostnames for result in results)
        assert all(result['Recommendation'] == OPENSSH_RECOMMENDATION for result in results)

        # Run the remediation for all hosts matching this rule
        timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.remediate(OPENSSH_RECOMMENDATION)

        def verify_tasks():
            tasks = session.task.search(f'{TASK_QUERY} and start_at >= "{timestamp}"')
            assert all(task['Result'] != 'error' for task in tasks)
            return len(tasks) == len(rhel_insights_vms) and all(
                task['Result'] == 'success' for task in tasks
            )

        # Wait for the remediation tasks to complete.
        wait_for(
            lambda: verify_tasks(),
            timeout=120,
            delay=15,
            handle_exception=True,
        )

        # Re-sync the recommendations
        sync_recommendations(session)

        # Verify that the recommendations are not listed anymore.
        assert not session.cloudinsights.search(REC_QUERY)


@pytest.mark.stubbed
def test_insights_reporting_status():
    """Verify that the Insights reporting status functionality works as expected.

    :id: 75629a08-b585-472b-a295-ce497075e519

    :steps:
        1. Register a satellite content host with insights.
        2. Change 48 hours of wait time to 4 minutes in insights_client_report_status.rb file.
            See foreman_rh_cloud PR#596.
        3. Unregister host from insights.
        4. Wait 4 minutes.
        5. Use ForemanTasks.sync_task(InsightsCloud::Async::InsightsClientStatusAging)
            execute task manually.

    :expectedresults:
        1. Insights status for host changed to "Not reporting".

    :CaseImportance: Medium

    :BZ: 1976853

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_recommendation_sync_for_satellite():
    """Verify that Insights recommendations are listed for satellite.

    :id: ee3feba3-c255-42f1-8293-b04d540dcca5

    :steps:
        1. Register Satellite with insights.(satellite-installer --register-with-insights)
        2. Add RH cloud token in settings.
        3. Go to Insights > Recommendations > Click on Sync recommendations button.
        4. Click on notification icon.
        5. Select recommendation and try remediating it.

    :expectedresults:
        1. Notification about insights recommendations for Satellite is shown.
        2. Insights recommendations are listed for satellite.
        3. Successfully remediated the insights recommendation for Satellite itself.

    :CaseImportance: High

    :BZ: 1978182

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_host_sorting_based_on_recommendation_count():
    """Verify that hosts can be sorted and filtered based on insights
        recommendation count.

    :id: b1725ec1-60db-422e-809d-f81d99ae156e

    :steps:
        1. Register few satellite content host with insights.
        2. Sync Insights recommendations.
        3. Go to Hosts > All Hosts.
        4. Click on "Recommendations" column.
        5. Use insights_recommendations_count keyword to filter hosts.

    :expectedresults:
        1. Hosts are sorted based on recommendations count.
        2. Hosts are filtered based on insights_recommendations_count.

    :CaseImportance: Low

    :BZ: 1889662

    :CaseAutomation: ManualOnly
    """


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-0')
def test_host_details_page(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Test host details page for host having insights recommendations.

    :id: e079ed10-c9f5-4331-9cb3-70b224b1a584

    :customerscenario: true

    :steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Sync Insights recommendations.
        3. Sync Insights inventory status.
        4. Go to Hosts -> All Hosts
        5. Verify there is a "Recommendations" column containing Insights recommendation count.
        6. Check popover status of host.
        7. Verify that host properties shows "reporting" inventory upload status.
        8. Read the recommendations listed in Insights tab present on host details page.
        9. Click on "Recommendations" tab.
        10. Try to delete host.

    :expectedresults:
        1. There's Insights column with number of recommendations.
        2. Inventory upload status is displayed in popover status of host.
        3. Insights registration status is displayed in popover status of host.
        4. Inventory upload status is present in host properties table.
        5. Verify the contents of Insights tab.
        6. Clicking on "Recommendations" tab takes user to Insights page with
            recommendations selected for that host.
        7. Host having Insights recommendations is deleted from Satellite.

    :BZ: 1974578, 1860422, 1928652, 1865876, 1879448

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Prepare misconfigured machine and upload data to Insights.
    create_insights_vulnerability(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Sync insights recommendations.
        sync_recommendations(session)

        # Verify Insights status of host.
        result = session.host_new.get_host_statuses(rhel_insights_vm.hostname)
        assert result['Insights']['Status'] == 'Reporting'
        assert result['Inventory']['Status'] == 'Successfully uploaded to your RH cloud inventory'

        # Verify recommendations exist for host.
        result = session.host_new.search(rhel_insights_vm.hostname)[0]
        assert result['Name'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) > 0

        # Read the recommendations in Insights tab on host details page.
        insights_recommendations = session.host_new.get_insights(rhel_insights_vm.hostname)[
            'recommendations_table'
        ]

        # Verify
        for recommendation in insights_recommendations:
            if recommendation['Recommendation'] == DNF_RECOMMENDATION:
                assert recommendation['Total risk'] == 'Moderate'
                assert DNF_RECOMMENDATION in recommendation['Recommendation']
                assert len(insights_recommendations) == int(result['Recommendations'])

        # Test Recommendation button present on host details page
        recommendations = session.host_new.get_insights(rhel_insights_vm.hostname)[
            'recommendations_table'
        ]
        assert len(recommendations), 'No recommendations were found'
        assert int(result['Recommendations']) == len(recommendations)

    # Delete host
    rhel_insights_vm.nailgun_host.delete()
    assert not rhel_insights_vm.nailgun_host


@pytest.mark.e2e
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list(r'^[\d]+$')
def test_insights_registration_with_capsule(
    rhcloud_capsule,
    rhcloud_activation_key,
    rhcloud_manifest_org,
    module_target_sat_insights,
    rhel_contenthost,
    default_os,
):
    """Registering host with insights having traffic going through
        external capsule and also test rh_cloud_insights:clean_statuses rake command.

    :id: 9db1d307-664c-4d4a-89de-da986224f071

    :customerscenario: true

    :steps:
        1. Integrate a capsule with satellite.
        2. open the global registration form and select the same capsule.
        3. Override Insights and Rex parameters.
        4. check host is registered successfully with selected capsule.
        5. Test insights client connection & reporting status.
        6. Run rh_cloud_insights:clean_statuses rake command
        7. Verify that host properties doesn't contain insights status.

    :expectedresults:
        1. Host is successfully registered with capsule host,
            having remote execution and insights.
        2. rake command deletes insights reporting status of host.

    :BZ: 2110222, 2112386, 1962930

    :parametrized: yes
    """
    org = rhcloud_manifest_org
    ak = rhcloud_activation_key
    # Enable rhel repos and install insights-client
    rhelver = rhel_contenthost.os_version.major
    if rhelver > 7:
        rhel_contenthost.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
    else:
        rhel_contenthost.create_custom_repos(
            **{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']}
        )
    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org.name)

        # Generate host registration command
        cmd = session.host_new.get_register_command(
            {
                'general.organization': org.name,
                'general.capsule': rhcloud_capsule.hostname,
                'general.activation_keys': ak.name,
                'general.insecure': True,
                'advanced.setup_insights': 'Yes (override)',
                'advanced.setup_rex': 'Yes (override)',
            }
        )
        # Register host with Satellite and Insights.
        rhel_contenthost.execute(cmd)
        assert rhel_contenthost.subscribed
        assert rhel_contenthost.execute('insights-client --test-connection').status == 0
        values = session.host_new.get_host_statuses(rhel_contenthost.hostname)
        assert values['Insights']['Status'] == 'Reporting'
        # Clean insights status
        result = module_target_sat_insights.run(
            f'foreman-rake rh_cloud_insights:clean_statuses SEARCH="{rhel_contenthost.hostname}"'
        )
        assert 'Deleted 1 insights statuses' in result.stdout
        assert result.status == 0
        # Workaround for not reading old data.
        session.browser.refresh()
        # Verify that Insights status is cleared.
        values = session.host_new.get_host_statuses(rhel_contenthost.hostname)
        assert values['Insights']['Status'] == 'N/A'
        result = rhel_contenthost.run('insights-client')
        assert result.status == 0
        # Workaround for not reading old data.
        session.browser.refresh()
        # Verify that Insights status again.
        values = session.host_new.get_host_statuses(rhel_contenthost.hostname)
        assert values['Insights']['Status'] == 'Reporting'
