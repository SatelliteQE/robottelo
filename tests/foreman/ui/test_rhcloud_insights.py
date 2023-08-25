"""Tests for RH Cloud - Inventory

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Team: Platform

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime

import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DNF_RECOMMENDATION
from robottelo.constants import OPENSSH_RECOMMENDATION


def create_insights_vulnerability(insights_vm):
    """Function to create vulnerabilities that can be remediated."""
    insights_vm.run(
        'chmod 777 /etc/ssh/sshd_config;dnf update -y dnf;'
        'sed -i -e "/^best/d" /etc/dnf/dnf.conf;insights-client'
    )


@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_rhcloud_insights_e2e(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat,
):
    """Synchronize hits data from cloud, verify it is displayed in Satellite and run remediation.

    :id: d952e83c-3faf-4299-a048-2eb6ccb8c9c2

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. In Satellite UI, go to Configure -> Insights -> Sync recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against host.
        4. Verify that the remediation job completed successfully.
        5. Sync Insights recommendations.
        6. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Remediation job finished successfully.
        3. Insights recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :BZ: 1965901, 1962048

    :customerscenario: true

    :parametrized: yes

    :CaseAutomation: Automated
    """
    job_query = (
        f'Remote action: Insights remediations for selected issues on {rhel_insights_vm.hostname}'
    )
    org = rhcloud_manifest_org
    # Prepare misconfigured machine and upload data to Insights
    create_insights_vulnerability(rhel_insights_vm)

    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        # Sync Insights recommendations
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        # Workaround for alert message causing search to fail. See airgun issue 584.
        session.browser.refresh()
        # Search for Insights recommendation.
        result = session.cloudinsights.search(
            f'hostname= "{rhel_insights_vm.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'
        )[0]
        assert result['Hostname'] == rhel_insights_vm.hostname
        assert result['Recommendation'] == OPENSSH_RECOMMENDATION
        # Run remediation and verify job completion.
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.remediate(OPENSSH_RECOMMENDATION)
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(query={'search': f'{job_query} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        # Search for Insights recommendations again.
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        # Workaround for alert message causing search to fail. See airgun issue 584.
        session.browser.refresh()
        # Verify that the insights recommendation is not listed anymore.
        assert not session.cloudinsights.search(
            f'hostname= "{rhel_insights_vm.hostname}" and title = "{OPENSSH_RECOMMENDATION}"'
        )


@pytest.mark.stubbed
def test_insights_reporting_status():
    """Verify that the Insights reporting status functionality works as expected.

    :id: 75629a08-b585-472b-a295-ce497075e519

    :Steps:
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

    :Steps:
        1. Register Satellite with insights.(satellite-installer --register-with-insights)
        2. Add RH cloud token in settings.
        3. Go to Configure > Insights > Click on Sync recommendations button.
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
def test_allow_auto_insights_sync_setting():
    """Test "allow_auto_insights_sync" setting.

    :id: ddc4ed5b-43c0-4121-bf2c-b8e040e45379

    :Steps:
        1. Register few satellite content host with insights.
        2. Enable "allow_auto_insights_sync" setting.
        3. Wait for "InsightsScheduledSync" task to run.

    :expectedresults:
        1. Satellite has "Inventory scheduled sync" recurring logic, which syncs
            inventory status automatically if "Automatic inventory upload" setting is enabled.

    :CaseImportance: Medium

    :BZ: 1865879

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_host_sorting_based_on_recommendation_count():
    """Verify that hosts can be sorted and filtered based on insights
        recommendation count.

    :id: b1725ec1-60db-422e-809d-f81d99ae156e

    :Steps:
        1. Register few satellite content host with insights.
        2. Sync Insights recommendations.
        3. Go to Hosts > All Host
        4. Click on "Recommendations" column.
        5. Use insights_recommendations_count keyword to filter hosts.

    :expectedresults:
        1. Hosts are sorted based on recommendations count.
        2. Hosts are filtered based on insights_recommendations_count.

    :CaseImportance: Low

    :BZ: 1889662

    :CaseAutomation: ManualOnly
    """


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_host_details_page(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat,
):
    """Test host details page for host having insights recommendations.

    :id: e079ed10-c9f5-4331-9cb3-70b224b1a584

    :customerscenario: true

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Sync insights recommendations.
        3. Sync RH Cloud inventory status.
        4. Go to Hosts -> All Hosts
        5. Verify there is a "Recommendations" column containing insights recommendation count.
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
        6. Clicking on "Recommendations" tab takes user to Insights page with insights
            recommendations selected for that host.
        7. Host having insights recommendations is deleted from Satellite.

    :BZ: 1974578, 1860422, 1928652, 1865876, 1879448

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org = rhcloud_manifest_org
    # Prepare misconfigured machine and upload data to Insights
    create_insights_vulnerability(rhel_insights_vm)
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Sync insights recommendations
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        # Verify Insights status of host.
        result = session.host.host_status(rhel_insights_vm.hostname)
        assert 'Insights: Reporting' in result
        assert 'Inventory: Successfully uploaded to your RH cloud inventory' in result
        result = session.host.search(rhel_insights_vm.hostname)[0]
        assert result['Name'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) > 0
        values = session.host.get_details(rhel_insights_vm.hostname)
        # Note: Reading host properties adds 'clear' to original value.
        assert (
            values['properties']['properties_table']['Inventory']
            == 'Successfully uploaded to your RH cloud inventory clear'
        )
        # Read the recommendations listed in Insights tab present on host details page
        insights_recommendations = session.host_new.insights_tab(rhel_insights_vm.hostname)
        for recommendation in insights_recommendations:
            if recommendation['name'] == DNF_RECOMMENDATION:
                assert recommendation['label'] == 'Moderate'
                assert DNF_RECOMMENDATION in recommendation['text']
                assert len(insights_recommendations) == int(result['Recommendations'])
        # Test Recommendation button present on host details page
        recommendations = session.host.read_insights_recommendations(rhel_insights_vm.hostname)
        assert len(recommendations), 'No recommendations were found'
        assert recommendations[0]['Hostname'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) == len(recommendations)
        # Delete host
        rhel_insights_vm.nailgun_host.delete()
        assert not rhel_insights_vm.nailgun_host


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_insights_registration_with_capsule(
    rhcloud_capsule,
    rhcloud_activation_key,
    rhcloud_manifest_org,
    module_target_sat,
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
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Generate host registration command
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.orgnization': org.name,
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
        values = session.host.get_details(rhel_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
        # Clean insights status
        result = module_target_sat.run(
            f'foreman-rake rh_cloud_insights:clean_statuses SEARCH="{rhel_contenthost.hostname}"'
        )
        assert 'Deleted 1 insights statuses' in result.stdout
        assert result.status == 0
        # Workaround for not reading old data.
        session.browser.refresh()
        # Verify that Insights status is cleared.
        values = session.host.get_details(rhel_contenthost.hostname)
        with pytest.raises(KeyError):
            values['properties']['properties_table']['Insights']
        result = rhel_contenthost.run('insights-client')
        assert result.status == 0
        # Workaround for not reading old data.
        session.browser.refresh()
        # Verify that Insights status again.
        values = session.host.get_details(rhel_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
