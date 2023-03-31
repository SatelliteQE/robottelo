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
from airgun.session import Session
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC


@pytest.mark.e2e
@pytest.mark.run_in_one_thread
@pytest.mark.tier3
@pytest.mark.rhel_ver_list([8, 9])
def test_rhcloud_insights_e2e(
    rhel_insights_vm,
    organization_ak_setup,
    rhcloud_sat_host,
):
    """Synchronize hits data from cloud, verify it is displayed in Satellite and run remediation.

    :id: d952e83c-3faf-4299-a048-2eb6ccb8c9c2

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. In Satellite UI, Configure -> Insights -> Sync recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against rhel8/rhel9 host.
        4. Assert that job completed successfully.
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
    org, ak = organization_ak_setup
    # Create a vulnerability which can be remediated
    rhel_insights_vm.run('chmod 777 /etc/ssh/sshd_config;insights-client')
    query = 'Decreased security: OpenSSH config permissions'
    job_query = (
        f'Remote action: Insights remediations for selected issues on {rhel_insights_vm.hostname}'
    )
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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
        result = session.cloudinsights.search(query)[0]
        assert result['Hostname'] == rhel_insights_vm.hostname
        assert result['Recommendation'] == query
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.remediate(query)
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
            .search(query={'search': f'{job_query} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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
        assert not session.cloudinsights.search(query)


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


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.rhel_ver_list([8])
def test_host_details_page(
    rhel_insights_vm,
    organization_ak_setup,
    rhcloud_sat_host,
):
    """Test host details page for host having insights recommendations.

    :id: e079ed10-c9f5-4331-9cb3-70b224b1a584

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Sync insights recommendations.
        3. Sync RH Cloud inventory status.
        4. Go to Hosts -> All Hosts
        5. Assert there is "Recommendations" column containing insights recommendation count.
        6. Check popover status of host.
        7. Assert that host properties shows reporting inventory upload status.
        8. Click on "Recommendations" tab.

    :expectedresults:
        1. There's Insights column with number of recommendations.
        2. Inventory upload status is displayed in popover status of host.
        3. Insights registration status is displayed in popover status of host.
        4. Inventory upload status is present in host properties table.
        5. Clicking on "Recommendations" tab takes user to Insights page with insights
            recommendations selected for that host.

    :BZ: 1974578

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    # Create a vulnerability which can be remediated
    rhel_insights_vm.run('dnf update -y dnf;sed -i -e "/^best/d" /etc/dnf/dnf.conf;insights-client')
    # Sync inventory status
    inventory_sync = rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_inventory_sync()
    wait_for(
        lambda: rhcloud_sat_host.api.ForemanTask()
        .search(query={'search': f'id = {inventory_sync["task"]["id"]}'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Sync insights recommendations
        session.cloudinsights.sync_hits()
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
        recommendations = session.host.read_insights_recommendations(rhel_insights_vm.hostname)
        assert len(recommendations), 'No recommendations were found'
        assert recommendations[0]['Hostname'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) == len(recommendations)


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_rh_cloud_insights_clean_statuses(
    rhel7_contenthost,
    rhel8_contenthost,
    organization_ak_setup,
    rhcloud_sat_host,
):
    """Test rh_cloud_insights:clean_statuses rake command.

    :id: 6416ed31-cafb-4278-b205-bf3da9ab2ee4

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights
        2. Go to Hosts -> All Hosts
        3. Assert that host properties shows reporting status for insights.
        4. Run rh_cloud_insights:clean_statuses rake command
        5. Assert that host properties doesn't contain insights status.

    :expectedresults:
        1. rake command deletes insights reporting status of host.

    :BZ: 1962930

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    rhel7_contenthost.configure_rhai_client(
        satellite=rhcloud_sat_host, activation_key=ak.name, org=org.label, rhel_distro='rhel7'
    )
    rhel8_contenthost.configure_rhai_client(
        satellite=rhcloud_sat_host, activation_key=ak.name, org=org.label, rhel_distro='rhel8'
    )
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        values = session.host.get_details(rhel7_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
        values = session.host.get_details(rhel8_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
        # Clean insights status
        result = rhcloud_sat_host.run(
            f'foreman-rake rh_cloud_insights:clean_statuses SEARCH="{rhel7_contenthost.hostname}"'
        )
        assert 'Deleted 1 insights statuses' in result.stdout
        assert result.status == 0
        values = session.host.get_details(rhel7_contenthost.hostname)
        with pytest.raises(KeyError):
            values['properties']['properties_table']['Insights']
        values = session.host.get_details(rhel8_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
        result = rhel7_contenthost.run('insights-client')
        assert result.status == 0
        values = session.host.get_details(rhel7_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.rhel_ver_list([8])
def test_delete_host_having_insights_recommendation(
    rhel_insights_vm,
    organization_ak_setup,
    rhcloud_sat_host,
):
    """Verify that host having insights recommendations can be deleted from Satellite.

    :id: 07914ff7-e230-4416-8664-7d357e9966f3

    :customerscenario: true

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Sync insights recommendations.
        3. Sync RH Cloud inventory status.
        4. Go to Hosts -> All Hosts
        5. Assert there is "Recommendations" column containing insights recommendation count.
        6. Try to delete host.

    :expectedresults:
        1. host having insights recommendations is deleted from Satellite.

    :CaseImportance: Critical

    :BZ: 1860422, 1928652

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    # Create a vulnerability which can be remediated
    rhel_insights_vm.run('dnf update -y dnf;sed -i -e "/^best/d" /etc/dnf/dnf.conf;insights-client')
    # Sync inventory status
    inventory_sync = rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_inventory_sync()
    wait_for(
        lambda: rhcloud_sat_host.api.ForemanTask()
        .search(query={'search': f'id = {inventory_sync["task"]["id"]}'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Sync insights recommendations
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
            .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        result = session.host.search(rhel_insights_vm.hostname)[0]
        assert result['Name'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) > 0
        values = session.host.get_details(rhel_insights_vm.hostname)
        # Note: Reading host properties adds 'clear' to original value.
        assert (
            values['properties']['properties_table']['Inventory']
            == 'Successfully uploaded to your RH cloud inventory clear'
        )
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
        # Delete host
        session.host.delete(rhel_insights_vm.hostname)
        assert not rhcloud_sat_host.api.Host().search(
            query={'search': f'name="{rhel_insights_vm.hostname}"'}
        )


@pytest.mark.tier2
@pytest.mark.rhel_ver_list([8])
def test_insights_tab_on_host_details_page(
    rhel_insights_vm,
    organization_ak_setup,
    rhcloud_sat_host,
):
    """Test recommendations count in hosts index is a link and contents
        of Insights tab on host details page.

    :id: d969ad38-7ee5-4c57-8538-1cf6c1705707

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. In Satellite UI, Configure -> Insights -> Sync now.
        3. Go to Hosts -> All Hosts.
        4. Click on recommendation count.
        5. Assert the contents of Insights tab.

    :expectedresults:
        1. There's Insights recommendation column with number of recommendations and
            link to Insights tab on host details page.
        2. Insights tab shows recommendations for the host.

    :CaseImportance: High

    :BZ: 1865876, 1879448

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    # Create a vulnerability which can be remediated
    rhel_insights_vm.run('dnf update -y dnf;sed -i -e "/^best/d" /etc/dnf/dnf.conf;insights-client')
    dnf_issue = (
        'The dnf installs lower versions of packages when the '
        '"best" option is not present in the /etc/dnf/dnf.conf'
    )
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Sync insights recommendations
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
            .search(query={'search': f'Insights full sync and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        result = session.host.search(rhel_insights_vm.hostname)[0]
        assert result['Name'] == rhel_insights_vm.hostname
        assert int(result['Recommendations']) > 0
        insights_recommendations = session.host.insights_tab(rhel_insights_vm.hostname)
        for recommendation in insights_recommendations:
            if recommendation['name'] == dnf_issue:
                assert recommendation['label'] == 'Moderate'
                assert dnf_issue in recommendation['text']
                assert len(insights_recommendations) == int(result['Recommendations'])


@pytest.mark.e2e
@pytest.mark.no_containers
def test_insights_registration_with_capsule(
    rhcloud_capsule, organization_ak_setup, rhcloud_sat_host, rhel7_contenthost, default_os
):
    """Registering host with insights having traffic going through
        external capsule.

    :id: 9db1d307-664c-4d4a-89de-da986224f071

    :customerscenario: true

    :steps:
        1. Integrate a capsule with satellite.
        2. open the global registration form and select the same capsule.
        3. Overide Insights and Rex parameters.
        4. check host is registered successfully with selected capsule.
        5. Test insights client connection & reporting status.

    :expectedresults: Host is successfully registered with capsule host,
             having remote execution and insights.

    :BZ: 2110222, 2112386
    """
    org, ak = organization_ak_setup
    capsule = rhcloud_sat_host.api.SmartProxy(name=rhcloud_capsule.hostname).search()[0]
    org.smart_proxy.append(capsule)
    org.update(['smart_proxy'])

    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
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
        # TODO: Make this test parametirzed for all rhel versions after verifying BZ:2129254
        rhel7_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
        assert rhel7_contenthost.execute('yum install -y insights-client').status == 0
        rhel7_contenthost.execute(cmd)
        assert rhel7_contenthost.subscribed
        assert rhel7_contenthost.execute('insights-client --test-connection').status == 0
        values = session.host.get_details(rhel7_contenthost.hostname)
        assert values['properties']['properties_table']['Insights'] == 'Reporting clear'
