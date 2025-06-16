"""Tests for RH Cloud - Inventory, also known as Insights Inventory Upload

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from datetime import UTC, datetime, timedelta

import pytest
from wait_for import wait_for

from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG
from robottelo.utils.io import (
    get_local_file_data,
    get_remote_report_checksum,
    get_report_data,
)


@pytest.fixture(scope='module', autouse=True)
def data_collection_default(module_target_sat):
    """Module scoped fixture to set default data collection setting to 'No'"""
    settings_object = module_target_sat.api.Setting().search(
        query={'search': 'name=insights_minimal_data_collection'}
    )[0]
    data_collection_value = settings_object.value
    settings_object.value = 'No'
    settings_object.update({'value'})
    yield
    settings_object.value = data_collection_value
    settings_object.update({'value'})


@pytest.fixture
def data_collection_minimal(module_target_sat):
    """Fixture to set minimal data collection setting to 'Yes'"""
    settings_object = module_target_sat.api.Setting().search(
        query={'search': 'name=insights_minimal_data_collection'}
    )[0]
    settings_object.value = 'Yes'
    settings_object.update({'value'})
    yield
    settings_object.value = 'No'
    settings_object.update({'value'})


def common_assertion(
    report_path, inventory_data, org, satellite, subscription_connection_enabled=True
):
    """Function to perform common assertions"""
    local_file_data = get_local_file_data(report_path)
    upload_success_msg = (
        f'Done: /var/lib/foreman/red_hat_inventory/uploads/report_for_{org.id}.tar.xz'
    )
    upload_error_messages = ['NSS error', 'Permission denied']

    assert 'Successfully generated' in inventory_data['generating']['terminal']
    if subscription_connection_enabled:
        assert upload_success_msg in inventory_data['uploading']['terminal']
        assert 'x-rh-insights-request-id' in inventory_data['uploading']['terminal'].lower()
        for error_msg in upload_error_messages:
            assert error_msg not in inventory_data['uploading']['terminal']
        # There is no uploaded report with subscription_connection_enabled set to false
        assert local_file_data['checksum'] == get_remote_report_checksum(satellite, org.id)

    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.run_in_one_thread
@pytest.mark.usefixtures('setting_update')
@pytest.mark.parametrize(
    'setting_update',
    ['subscription_connection_enabled=true', 'subscription_connection_enabled=false'],
    indirect=True,
)
def test_rhcloud_inventory_e2e(
    inventory_settings,
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
    setting_update,
):
    """Generate report and verify its basic properties,
    also test with subscription_connection_enabled setting set to true and false.

    :id: 833bd61d-d6e7-4575-887a-9e0729d0fa76

    :parametrized: yes

    :customerscenario: true

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar
        7. Host counts in metadata matches host counts in slices
        8. Assert Hostnames, IP addresses, and installed packages are present in the report.

    :CaseImportance: Critical

    :BZ: 1807829, 1926100
    """
    subscription_setting = setting_update.value == 'true'
    org = rhcloud_manifest_org
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
    # Verify that generated archive is valid.
    common_assertion(report_path, inventory_data, org, module_target_sat, subscription_setting)
    # Get report data for assertion
    json_data = get_report_data(report_path)
    # Verify that hostnames are present in the report.
    hostnames = [host['fqdn'] for host in json_data['hosts']]
    assert virtual_host.hostname in hostnames
    assert baremetal_host.hostname in hostnames
    # Verify that ip_addresses are present report.
    ip_addresses = [
        host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
        for host in json_data['hosts']
    ]
    ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
    assert virtual_host.ip_addr in ip_addresses
    assert baremetal_host.ip_addr in ip_addresses
    assert virtual_host.ip_addr in ipv4_addresses
    assert baremetal_host.ip_addr in ipv4_addresses
    # Verify that packages are included in report
    all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
    for host_profiles in all_host_profiles:
        assert 'installed_packages' in host_profiles
        assert len(host_profiles['installed_packages']) > 1


@pytest.mark.run_in_one_thread
def test_rh_cloud_inventory_settings(
    module_target_sat,
    inventory_settings,
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
):
    """Test whether `Obfuscate host names`, `Obfuscate host ipv4 addresses`
        and `Exclude Packages` setting works as expected.

    :id: 3c3a36b6-6566-446b-b803-3f8f9aab2511

    :customerscenario: true

    :steps:

        1. Prepare machine and upload its data to Insights.
        2. Go to Insights > Inventory upload > enable “Obfuscate host names” setting.
        3. Go to Insights > Inventory upload > enable “Obfuscate host ipv4 addresses” setting.
        4. Go to Insights > Inventory upload > enable “Exclude Packages” setting.
        5. Generate report after enabling the settings.
        6. Check if host names are obfuscated in generated reports.
        7. Check if hosts ipv4 addresses are obfuscated in generated reports.
        8. Check if packages are excluded from generated reports.
        9. Disable previous setting.
        10. Go to Administer > Settings > RH Cloud and enable "Obfuscate host names" setting.
        11. Go to Administer > Settings > RH Cloud and enable "Obfuscate IPs" setting.
        12. Go to Administer > Settings > RH Cloud and enable
            "Don't upload installed packages" setting.
        13. Generate report after enabling the setting.
        14. Check if host names are obfuscated in generated reports.
        15. Check if hosts ipv4 addresses are obfuscated in generated reports.
        16. Check if packages are excluded from generated reports.

    :expectedresults:
        1. Obfuscated host names in reports generated.
        2. Obfuscated host ipv4 addresses in generated reports.
        3. Packages are excluded from reports generated.

    :BZ: 1852594, 1889690, 1852594

    :CaseAutomation: Automated
    """
    org = rhcloud_manifest_org
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Enable settings on inventory page.
        session.cloudinventory.update({'obfuscate_hostnames': True})
        session.cloudinventory.update({'obfuscate_ips': True})
        session.cloudinventory.update({'exclude_packages': True})
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
        # Verify settings are enabled.
        assert inventory_data['obfuscate_hostnames'] is True
        assert inventory_data['obfuscate_ips'] is True
        assert inventory_data['exclude_packages'] is True
        # Verify that generated archive is valid.
        common_assertion(report_path, inventory_data, org, module_target_sat)
        # Get report data for assertion
        json_data = get_report_data(report_path)
        # Verify that hostnames are obfuscated from the report.
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname not in hostnames
        assert baremetal_host.hostname not in hostnames
        # Verify that ip_addresses are obfuscated from the report.
        ip_addresses = [
            host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
            for host in json_data['hosts']
        ]
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr not in ip_addresses
        assert baremetal_host.ip_addr not in ip_addresses
        assert virtual_host.ip_addr not in ipv4_addresses
        assert baremetal_host.ip_addr not in ipv4_addresses
        # Verify that packages are excluded from report
        all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
        for host_profiles in all_host_profiles:
            assert 'installed_packages' not in host_profiles
        # Disable settings on inventory page.
        session.cloudinventory.update({'obfuscate_hostnames': False})
        session.cloudinventory.update({'obfuscate_ips': False})
        session.cloudinventory.update({'exclude_packages': False})
        # Enable settings, the one on the main settings page.
        module_target_sat.update_setting('obfuscate_inventory_hostnames', True)
        module_target_sat.update_setting('obfuscate_inventory_ips', True)
        module_target_sat.update_setting('exclude_installed_packages', True)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
        # Verify settings are enabled.
        assert inventory_data['obfuscate_hostnames'] is True
        assert inventory_data['obfuscate_ips'] is True
        assert inventory_data['exclude_packages'] is True
        # Get report data for assertion
        json_data = get_report_data(report_path)
        # Verify that hostnames are obfuscated from the report.
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname not in hostnames
        assert baremetal_host.hostname not in hostnames
        # Verify that ip_addresses are obfuscated from the report.
        ip_addresses = [
            host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
            for host in json_data['hosts']
        ]
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr not in ip_addresses
        assert baremetal_host.ip_addr not in ip_addresses
        assert virtual_host.ip_addr not in ipv4_addresses
        assert baremetal_host.ip_addr not in ipv4_addresses
        # Verify that packages are excluded from report
        all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
        for host_profiles in all_host_profiles:
            assert 'installed_packages' not in host_profiles


@pytest.mark.stubbed
def test_failed_inventory_upload():
    """Verify that the failed report upload is indicated 'X' icon on Inventory upload page.

    :id: 230d3fc3-2810-4385-b07b-30f9bf632488

    :steps:
        1. Register a satellite content host with insights.
        2. Change 'DEST' from /var/lib/foreman/red_hat_inventory/uploads/uploader.sh
            to an invalid url.
        3. Go to Insights > Inventory upload > Click on restart button.

    :expectedresults:
        1. Inventory report upload failed.
        2. Failed upload is indicated by 'X' icon.

    :CaseImportance: Medium

    :BZ: 1830026

    :CaseAutomation: ManualOnly
    """


def test_rhcloud_inventory_without_manifest(session, module_org, target_sat):
    """Verify that proper error message is given when no manifest is imported in an organization.

    :id: 1d90bb24-2380-4653-8ed6-a084fce66d1e

    :steps:
        1. Don't import manifest to satellite.
        3. Go to Insights > Inventory upload > Click on restart button.

    :expectedresults:
        1. No stacktrace in production.log
        2. Message "Skipping organization '<redacted>', no candlepin certificate defined." is shown.

    :CaseImportance: Medium

    :BZ: 1842903

    :CaseAutomation: Automated
    """
    with session:
        session.organization.select(org_name=module_org.name)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(module_org.name)
        wait_for(
            lambda: target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        inventory_data = session.cloudinventory.read(module_org.name)
    assert (
        f'Skipping organization {module_org.name}, no candlepin certificate defined.'
        in inventory_data['uploading']['terminal']
    )


@pytest.mark.parametrize("module_target_sat_insights", [False], ids=["local"], indirect=True)
def test_rhcloud_inventory_disabled_local_insights(module_target_sat_insights):
    """Verify that the 'Insights > Inventory Upload' navigation item is not available
    when the Satellite is configured to use a local advisor engine.

    :id: 84023ae9-7bc4-4332-9aaf-749d6c48c2d2

    :steps:
        1. Configure Satellite to use local Insights advisor engine.
        2. Navigate to the Insights Recommendations page.
        3. Select Insights > Inventory Upload from the navigation menu.

    :expectedresults:
        1. "Inventory Upload" is not visible under "Insights".

    :CaseImportance: Medium

    :CaseAutomation: Automated
    """
    with module_target_sat_insights.ui_session() as session:
        insights_view = session.cloudinsights.navigate_to(session.cloudinsights, 'All')
        with pytest.raises(Exception, match='not found in navigation tree'):
            insights_view.menu.select('Insights', 'Inventory Upload')


@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.run_in_one_thread
def test_rhcloud_global_parameters(
    inventory_settings,
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
):
    """Verify that the host_registration_insights parameters are seperate from the
        Satellite Inventory Plugin by setting host_registration_inventory_plugin to false and
        generating a report

    :id: c5b22117-2022-4014-9e1e-b7d26de2360e

    :steps:
        1. Configure Satellite and hosts for insights registration
        2. Set the global parameter host_registration_insights_inventory to false
        3. Generate and download insights report
        4. Verify the report does not contain hosts(empty)
        5. Set the global parameter host_registration_insights_inventory to true
        6. Verify the report does contain the hosts


    :customerscenario: true

    :Verifies: SAT-27221

    :expectedresults: Setting the host_registration_inventory_plugin should remove hosts from
        the report
    """
    org = rhcloud_manifest_org
    virtual_host, baremetal_host = rhcloud_registered_hosts
    # Set the global parameter 'host_registration_insights_inventory' to false
    insights_cp = (
        module_target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights_inventory'})[0]
        .read()
    )
    module_target_sat.api.CommonParameter(id=insights_cp.id, value='false').update(['value'])
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
    # Verify that generated archive is valid
    common_assertion(report_path, inventory_data, org, module_target_sat)
    # Get report data for assertion
    json_data = get_report_data(report_path)
    # Verify that hostnames are not in report(empty)
    assert json_data == {}
    # Set the global parameter 'host_registration_insights_inventory' back to true
    insights_cp = (
        module_target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights_inventory'})[0]
        .read()
    )
    module_target_sat.api.CommonParameter(id=insights_cp.id, value='true').update(['value'])
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
    # Verify that generated archive is valid
    common_assertion(report_path, inventory_data, org, module_target_sat)
    # Get report data for assertion
    json_data = get_report_data(report_path)
    # Verify that hostnames are present in the report
    hostnames = [host['fqdn'] for host in json_data['hosts']]
    assert virtual_host.hostname in hostnames
    assert baremetal_host.hostname in hostnames


@pytest.mark.usefixtures('setting_update')
@pytest.mark.parametrize(
    'setting_update',
    ['subscription_connection_enabled=true', 'subscription_connection_enabled=false'],
    indirect=True,
)
def test_subscription_connection_settings_ui_behavior(request, module_target_sat, setting_update):
    """Verify that the RH Cloud Inventory UI
    reflects the subscription_connection_enabled setting

    :id: 9b8648b5-0ffb-49c1-a19e-04a7a8ce896f

    :parametrized: yes

    :steps:
        1. Set the subscription_connection_enabled setting to true
        2. Check that all the RH inventory settings, auto_upload and manual_upload descriptions,
            cloud_connector, uploading tab and sync_status buttons are displayed in the UI
        3. Set the subscription_connection_enabled setting to false
        4. Verify that auto_update switch, auto_upload and manual_upload descriptions, uploading tab,
            configure_cloud_connector and sync_all buttons are NOT displayed in the UI

    :expectedresults:
        1. The subscription_connection_enabled setting is reflected in the UI
    """
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=DEFAULT_ORG)
        session.location.select(loc_name=DEFAULT_LOC)

        displayed_inventory_data = session.cloudinventory.read_org(DEFAULT_ORG)
        displayed_settings_options = session.cloudinventory.get_displayed_settings_options()
        displayed_buttons = session.cloudinventory.get_displayed_buttons()
        displayed_descriptions = session.cloudinventory.get_displayed_descriptions()
        displayed_inventory_tabs = session.cloudinventory.get_displayed_inventory_tabs()

        subscription_setting = setting_update.value == 'true'

        assert displayed_settings_options['auto_update'] is subscription_setting
        assert displayed_buttons['cloud_connector'] is subscription_setting
        assert displayed_buttons['sync_status'] is subscription_setting
        assert displayed_descriptions['auto_upload_desc'] is subscription_setting
        assert displayed_descriptions['manual_upload_desc'] is subscription_setting
        assert displayed_inventory_tabs['uploading'] is subscription_setting
        assert (
            displayed_inventory_data['generating']['generate'] == 'Generate and upload report'
            if subscription_setting
            else 'Generate report'
        )


@pytest.mark.no_containers
@pytest.mark.run_in_one_thread
def test_rh_cloud_minimal_report(
    module_target_sat,
    inventory_settings,
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    data_collection_minimal,
):
    """Verify that the Minimal data collection report contains the proper fields

    :id: e9bd1b9f-705f-47de-8495-49618e019e8a

    :customerscenario: true

    :steps:

        1. Prepare machine and upload its data to Insights
        2. Go to Insights > Inventory upload > enable “Minimal data collection” setting
        3. Generate report after enabling the setting
        4. Check if hostnames are NOT in generated report
        5. Check if ipv4 addresses are NOT in generated reports
        6. Check if account, subscription_manager_id, insights_id, and installed_products fields are in report


    :expectedresults:
        1. Hostnames are NOT in generated report.
        2. Ipv4 addresses are NOT in generated report.
        3. Account, subscription_manager_id, insights_id, and installed_products fields are in report

    :Verifies: SAT-31467
    """
    org = rhcloud_manifest_org
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        session.cloudinventory.update(
            {
                'data_collection': 'Minimal data collectionOnly send the minimum required data to Red Hat cloud, obfuscation settings are disabled'
            }
        )
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish
        wait_for(
            lambda: module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'label = ForemanInventoryUpload::Async::GenerateReportJob '
                    f'and started_at >= "{timestamp}"'
                }
            )[0]
            .result
            == 'success',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        report_path = session.cloudinventory.download_report(org.name)
        inventory_data = session.cloudinventory.read(org.name)
        # Verify that generated archive is valid
        common_assertion(report_path, inventory_data, org, module_target_sat)
        # Get report data for assertion
        json_data = get_report_data(report_path)
        # Verify that hostnames are NOT in report
        host_data = [item for item in json_data['hosts']]
        hostnames = [item['fqdn'] for item in host_data if 'fqdn' in item]
        assert virtual_host.hostname not in hostnames, f"'hostname' found in: {hostnames}"
        assert baremetal_host.hostname not in hostnames, f"'hostname' found in: {hostnames}"
        # Verify that ip addresses are NOT in report
        ip_address = [item['ip_addresses'] for item in host_data if 'ip_addresses' in item]
        assert not ip_address, f"'ip_addresses' found in: {ip_address}"
        # Verify that installed_products are IN report
        system_profile = [item.get('system_profile', {}) for item in host_data]
        assert all('installed_products' in item for item in system_profile), (
            "'installed_products' is missing in one or more entries"
        )
        # Verify that proper fields are IN report
        required_fields = ['account', 'subscription_manager_id', 'insights_id']
        assert all(all(key in item for key in required_fields) for item in host_data), (
            "Not all required keys are present in every dictionary"
        )
