"""Tests for RH Cloud - Inventory, also known as Insights Inventory Upload

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta

import pytest
from airgun.session import Session
from wait_for import wait_for

from robottelo.constants import DEFAULT_LOC
from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_remote_report_checksum
from robottelo.rh_cloud_utils import get_report_data


def common_assertion(report_path, inventory_data, org, satellite):
    """Function to perform common assertions"""
    local_file_data = get_local_file_data(report_path)
    upload_success_msg = (
        f'Done: /var/lib/foreman/red_hat_inventory/uploads/report_for_{org.id}.tar.xz'
    )
    upload_error_messages = ['NSS error', 'Permission denied']

    assert 'Successfully generated' in inventory_data['generating']['terminal']
    assert upload_success_msg in inventory_data['uploading']['terminal']
    assert 'x-rh-insights-request-id' in inventory_data['uploading']['terminal'].lower()
    for error_msg in upload_error_messages:
        assert error_msg not in inventory_data['uploading']['terminal']

    assert local_file_data['checksum'] == get_remote_report_checksum(satellite, org.id)
    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_rhcloud_inventory_e2e(
    inventory_settings, organization_ak_setup, rhcloud_registered_hosts, rhcloud_sat_host
):
    """Generate report and verify its basic properties

    :id: 833bd61d-d6e7-4575-887a-9e0729d0fa76

    :customerscenario: true

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar
        7. Host counts in metadata matches host counts in slices
        8. Assert Hostnames, IP addresses, and installed packages are present in report.

    :CaseImportance: Critical

    :BZ: 1807829, 1926100
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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

    common_assertion(report_path, inventory_data, org, rhcloud_sat_host)
    json_data = get_report_data(report_path)
    hostnames = [host['fqdn'] for host in json_data['hosts']]
    assert virtual_host.hostname in hostnames
    assert baremetal_host.hostname in hostnames
    ip_addresses = [
        host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
        for host in json_data['hosts']
    ]
    ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
    assert virtual_host.ip_addr in ip_addresses
    assert baremetal_host.ip_addr in ip_addresses
    assert virtual_host.ip_addr in ipv4_addresses
    assert baremetal_host.ip_addr in ipv4_addresses
    all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
    for host_profiles in all_host_profiles:
        assert 'installed_packages' in host_profiles
        assert len(host_profiles['installed_packages']) > 1


@pytest.mark.stubbed
def test_hosts_synchronization():
    """Synchronize list of available hosts from cloud and mark them in Satellite

    :id: 2f1bdd42-140d-46f8-bad5-299c54620ee8

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. In Satellite UI, Configure -> Inventory upload -> Sync inventory status
        4. Assert content of toast message once synchronization finishes
        5. Go to Hosts -> All Hosts and assert content of status popover
        6. Open host page and assert status on "Properties" tab

    :expectedresults:
        1. Toast message contains number of hosts synchronized and missed
        2. Presence in cloud is displayed in popover status of host
        3. Presence in cloud is displayed in "Properties" tab on single host page

    :BZ: 1865874

    :CaseAutomation: NotAutomated
    """


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_obfuscate_host_names(
    rhcloud_sat_host, inventory_settings, organization_ak_setup, rhcloud_registered_hosts
):
    """Test whether `Obfuscate host names` setting works as expected.

    :id: 3c3a36b6-6566-446b-b803-3f8f9aab2511

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Obfuscate host names” setting.
        4. Generate report after enabling the setting.
        5. Check if host names are obfuscated in generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable "Obfuscate host names" setting.
        8. Generate report after enabling the setting.
        9. Check if host names are obfuscated in generated reports.

    :expectedresults:
        1. Obfuscated host names in reports generated.

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Enable obfuscate_hostnames setting on inventory page.
        session.cloudinventory.update({'obfuscate_hostnames': True})
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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

        # Assert that obfuscate_hostnames is enabled.
        assert inventory_data['obfuscate_hostnames'] is True
        # Assert that generated archive is valid.
        common_assertion(report_path, inventory_data, org, rhcloud_sat_host)
        # Get report data for assertion
        json_data = get_report_data(report_path)
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname not in hostnames
        assert baremetal_host.hostname not in hostnames
        # Assert that host ip_addresses are present in the report.
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr in ipv4_addresses
        assert baremetal_host.ip_addr in ipv4_addresses
        # Disable obfuscate_hostnames setting on inventory page.
        session.cloudinventory.update({'obfuscate_hostnames': False})

        # Enable obfuscate_hostnames setting.
        rhcloud_sat_host.update_setting('obfuscate_inventory_hostnames', True)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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

        assert inventory_data['obfuscate_hostnames'] is True
        json_data = get_report_data(report_path)
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname not in hostnames
        assert baremetal_host.hostname not in hostnames
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr in ipv4_addresses
        assert baremetal_host.ip_addr in ipv4_addresses


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_obfuscate_host_ipv4_addresses(
    rhcloud_sat_host, inventory_settings, organization_ak_setup, rhcloud_registered_hosts
):
    """Test whether `Obfuscate host ipv4 addresses` setting works as expected.

    :id: c0fc4ee9-a6a1-42c0-83f0-0f131ca9ab41

    :customerscenario: true

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Obfuscate host ipv4 addresses” setting.
        4. Generate report after enabling the setting.
        5. Check if hosts ipv4 addresses are obfuscated in generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable "Obfuscate IPs" setting.
        8. Generate report after enabling the setting.
        9. Check if hosts ipv4 addresses are obfuscated in generated reports.

    :expectedresults:
        1. Obfuscated host ipv4 addresses in generated reports.

    :BZ: 1852594, 1889690

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Enable obfuscate_ips setting on inventory page.
        session.cloudinventory.update({'obfuscate_ips': True})
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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
        # Assert that obfuscate_ips is enabled.
        assert inventory_data['obfuscate_ips'] is True
        # Assert that generated archive is valid.
        common_assertion(report_path, inventory_data, org, rhcloud_sat_host)
        # Get report data for assertion
        json_data = get_report_data(report_path)
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname in hostnames
        assert baremetal_host.hostname in hostnames
        # Assert that ip_addresses are obfuscated from report.
        ip_addresses = [
            host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
            for host in json_data['hosts']
        ]
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr not in ip_addresses
        assert baremetal_host.ip_addr not in ip_addresses
        assert virtual_host.ip_addr not in ipv4_addresses
        assert baremetal_host.ip_addr not in ipv4_addresses
        # Disable obfuscate_ips setting on inventory page.
        session.cloudinventory.update({'obfuscate_ips': False})

        # Enable obfuscate_inventory_ips setting.
        rhcloud_sat_host.update_setting('obfuscate_inventory_ips', True)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        # wait_for_tasks report generation task to finish.
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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

        assert inventory_data['obfuscate_ips'] is True
        # Get report data for assertion
        json_data = get_report_data(report_path)
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname in hostnames
        assert baremetal_host.hostname in hostnames
        ip_addresses = [
            host['system_profile']['network_interfaces'][0]['ipv4_addresses'][0]
            for host in json_data['hosts']
        ]
        ipv4_addresses = [host['ip_addresses'][0] for host in json_data['hosts']]
        assert virtual_host.ip_addr not in ip_addresses
        assert baremetal_host.ip_addr not in ip_addresses
        assert virtual_host.ip_addr not in ipv4_addresses
        assert baremetal_host.ip_addr not in ipv4_addresses


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_exclude_packages_setting(
    rhcloud_sat_host, inventory_settings, organization_ak_setup, rhcloud_registered_hosts
):
    """Test whether `Exclude Packages` setting works as expected.

    :id: 646093fa-fdd6-4f70-82aa-725e31fa3f12

    :customerscenario: true

    :Steps:

        1. Prepare machine and upload its data to Insights
        2. Add Cloud API key in Satellite
        3. Go to Configure > Inventory upload > enable “Exclude Packages” setting.
        4. Generate report after enabling the setting.
        5. Check if packages are excluded from generated reports.
        6. Disable previous setting.
        7. Go to Administer > Settings > RH Cloud and enable
            "Don't upload installed packages" setting.
        8. Generate report after enabling the setting.
        9. Check if packages are excluded from generated reports.

    :expectedresults:
        1. Packages are excluded from reports generated.

    :BZ: 1852594

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    with Session(hostname=rhcloud_sat_host.hostname) as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Enable exclude_packages setting on inventory page.
        session.cloudinventory.update({'exclude_packages': True})
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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
        assert inventory_data['exclude_packages'] is True
        # Disable exclude_packages setting on inventory page.
        session.cloudinventory.update({'exclude_packages': False})
        # Assert that generated archive is valid.
        common_assertion(report_path, inventory_data, org, rhcloud_sat_host)
        # Get report data for assertion
        json_data = get_report_data(report_path)
        # Assert that right hosts are present in report.
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname in hostnames
        assert baremetal_host.hostname in hostnames
        # Assert that packages are excluded from report
        all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
        for host_profiles in all_host_profiles:
            assert 'installed_packages' not in host_profiles

        # Enable exclude_installed_packages setting.
        rhcloud_sat_host.update_setting('exclude_installed_packages', True)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(org.name)
        wait_for(
            lambda: rhcloud_sat_host.api.ForemanTask()
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
        assert inventory_data['exclude_packages'] is True
        json_data = get_report_data(report_path)
        hostnames = [host['fqdn'] for host in json_data['hosts']]
        assert virtual_host.hostname in hostnames
        assert baremetal_host.hostname in hostnames
        all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
        for host_profiles in all_host_profiles:
            assert 'installed_packages' not in host_profiles


@pytest.mark.stubbed
def test_failed_inventory_upload():
    """Verify that the failed report upload is indicated 'X' icon on Inventory upload page.

    :id: 230d3fc3-2810-4385-b07b-30f9bf632488

    :Steps:
        1. Register a satellite content host with insights.
        2. Change 'DEST' from /var/lib/foreman/red_hat_inventory/uploads/uploader.sh
            to an invalid url.
        3. Go to Configure > Inventory upload > Click on restart button.

    :expectedresults:
        1. Inventory report upload failed.
        2. Failed upload is indicated by 'X' icon.

    :CaseImportance: Medium

    :BZ: 1830026

    :CaseAutomation: ManualOnly
    """


@pytest.mark.tier2
def test_rhcloud_inventory_without_manifest(session, module_org, default_sat):
    """Verify that proper error message is given when no manifest is imported in an organization.

    :id: 1d90bb24-2380-4653-8ed6-a084fce66d1e

    :Steps:
        1. Don't import manifest to satellite.
        3. Go to Configure > Inventory upload > Click on restart button.

    :expectedresults:
        1. No stacktrace in production.log
        2. Message "Skipping organization '<redacted>', no candlepin certificate defined." is shown.

    :CaseImportance: Medium

    :BZ: 1842903

    :CaseAutomation: Automated
    """
    with session:
        session.organization.select(org_name=module_org.name)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinventory.generate_report(module_org.name)
        wait_for(
            lambda: default_sat.api.ForemanTask()
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


@pytest.mark.stubbed
def test_automatic_inventory_upload_enabled_setting():
    """Test "Automatic inventory upload" setting.

    :id: e84790c6-1700-46c4-9bf8-d8f1e63a7f1f

    :Steps:
        1. Register satellite content host with insights.
        2. Sync inventory status.
        3. Wait for "Inventory scheduled sync" task to execute.
            (Change wait time to 1 minute for testing.)
        4. Check whether the satellite shows successful inventory upload for the host.
        5. Disable "Automatic inventory upload" setting.
        6. Unregister host from insights OR Delete host from cloud.
        7. Wait for "Inventory scheduled sync" task to execute.

    :expectedresults:
        1. When "Automatic inventory upload" setting is disabled then
            "Inventory scheduled sync" task doesn't sync the inventory status.

    :CaseImportance: Medium

    :BZ: 1965239

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_automatic_inventory_upload_disabled_setting():
    """Test "Automatic inventory upload" setting.

    :id: 2c830833-3f92-497c-bbb9-f485a1d8eb47

    :Steps:
        1. Register few hosts with satellite.
        2. Enable "Automatic inventory upload" setting.
        3. Wait for "Inventory scheduled sync" recurring logic to run.

    :expectedresults:
        1. Satellite has "Inventory scheduled sync" recurring logic, which syncs
            inventory status automatically if "Automatic inventory upload" setting is enabled.

    :CaseImportance: Medium

    :BZ: 1962695

    :CaseAutomation: ManualOnly
    """
