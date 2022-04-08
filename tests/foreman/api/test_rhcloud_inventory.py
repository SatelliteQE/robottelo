"""API tests for RH Cloud - Inventory, also known as Insights Inventory Upload

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: addubey

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime

import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string
from wait_for import wait_for

from robottelo.config import robottelo_tmp_dir
from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_report_data
from robottelo.rh_cloud_utils import get_report_metadata

generate_report_task = 'ForemanInventoryUpload::Async::UploadReportJob'


def generate_inventory_report(satellite, org):
    """Function to generate inventory report."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    satellite.api.Organization(id=org.id).rh_cloud_generate_report()
    wait_for(
        lambda: satellite.api.ForemanTask()
        .search(query={'search': f'{generate_report_task} and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )


def common_assertion(report_path):
    """Function to perform common assertions"""
    local_file_data = get_local_file_data(report_path)

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
def test_rhcloud_inventory_api_e2e(
    inventory_settings, organization_ak_setup, rhcloud_registered_hosts, rhcloud_sat_host
):
    """Generate report using rh_cloud plugin api's and verify its basic properties.

    :id: 8ead1ff6-a8f5-461b-9dd3-f50d96d6ed57

    :expectedresults:

        1. Report can be generated
        2. Report can be downloaded
        3. Report has non-zero size
        4. Report can be extracted
        5. JSON files inside report can be parsed
        6. metadata.json lists all and only slice JSON files in tar
        7. Host counts in metadata matches host counts in slices
        8. metadata contains source and foreman_rh_cloud_version keys.
        9. Assert Hostnames, IP addresses, infrastructure type, and installed packages
            are present in report.

    :CaseImportance: Critical

    :BZ: 1807829, 1926100, 1965234, 1824183, 1879453
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    local_report_path = robottelo_tmp_dir.joinpath(f'{gen_alphanumeric()}_{org.id}.tar.xz')
    # Generate report
    generate_inventory_report(rhcloud_sat_host, org)
    # Download report
    rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_download_report(
        destination=local_report_path
    )
    common_assertion(local_report_path)
    # Assert Hostnames, IP addresses, and installed packages are present in report.
    json_data = get_report_data(local_report_path)
    json_meta_data = get_report_metadata(local_report_path)
    package_version = rhcloud_sat_host.run('rpm -qa --qf "%{VERSION}" tfm-rubygem-foreman_rh_cloud')

    assert json_meta_data['source_metadata']['foreman_rh_cloud_version'] == str(package_version)
    assert json_meta_data['source'] == 'Satellite'
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

    infrastructure_type = [
        host['system_profile']['infrastructure_type'] for host in json_data['hosts']
    ]
    assert 'physical' and 'virtual' in infrastructure_type

    all_host_profiles = [host['system_profile'] for host in json_data['hosts']]
    for host_profiles in all_host_profiles:
        assert 'installed_packages' in host_profiles
        assert len(host_profiles['installed_packages']) > 1


@pytest.mark.tier3
def test_rhcloud_inventory_api_hosts_synchronization(
    set_rh_cloud_token,
    organization_ak_setup,
    rhcloud_registered_hosts,
    rhcloud_sat_host,
):
    """Test RH Cloud plugin api to synchronize list of available hosts from cloud.

    :id: 7be22e1c-906b-4ae5-93dd-5f79f395601c

    :Steps:

        1. Prepare machine and upload its data to Insights.
        2. Add Cloud API key in Satellite
        3. Sync inventory status using RH Cloud plugin api.
        4. Assert content of finished tasks.
        5. Get host details.
        6. Assert inventory status for the host.

    :expectedresults:
        1. Task detail should contain should contain number of hosts
            synchronized and disconnected.

    :BZ: 1970223

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    # Generate report
    generate_inventory_report(rhcloud_sat_host, org)
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
    task_output = rhcloud_sat_host.api.ForemanTask().search(
        query={'search': f'id = {inventory_sync["task"]["id"]}'}
    )
    assert task_output[0].output['host_statuses']['sync'] == 2
    assert task_output[0].output['host_statuses']['disconnect'] == 0
    # To Do: Add support in Nailgun to get Insights and Inventory host properties.


@pytest.mark.stubbed
def test_rhcloud_inventory_mtu_field():
    """Verify that the hosts having mtu field value as string in foreman's Nic object
    is present in the inventory report.

    :id: df6d5f4f-5ee1-4f34-bf24-b93fbd089322

    :customerscenario: true

    :Steps:
        1. Register a content host.
        2. If value of mtu field is not a string then use foreman-rake to change it.
        3. Generate inventory report.
        4. Assert that host is listed in the inventory report.
        5. Assert that value of mtu field in generated report is a number.

    :CaseImportance: Medium

    :expectedresults:
        1. Host having string mtu field value is present in the inventory report.
        2. Value of mtu field in generated inventory report is a number.

    :BZ: 1893439

    :CaseAutomation: NotAutomated
    """


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_system_purpose_sla_field(
    inventory_settings, organization_ak_setup, rhcloud_registered_hosts, rhcloud_sat_host
):
    """Verify that system_purpose_sla field is present in the inventory report
    for the host subscribed using Activation key with service level set in it.

    :id: 3974338c-3a66-41ac-af32-ee76e3c37aef

    :customerscenario: true

    :Steps:
        1. Create an activation key with service level set in it.
        2. Register a content host using the created activation key.
        3. Generate inventory report.
        4. Assert that host is listed in the inventory report.
        5. Assert that system_purpose_sla field is present in the inventory report.

    :CaseImportance: Medium

    :expectedresults:
        1. Host is present in the inventory report.
        2. system_purpose_sla field is present in the inventory report.

    :BZ: 1845113

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    local_report_path = robottelo_tmp_dir.joinpath(f'{gen_alphanumeric()}_{org.id}.tar.xz')
    generate_inventory_report(rhcloud_sat_host, org)
    # Download report
    rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_download_report(
        destination=local_report_path
    )
    json_data = get_report_data(local_report_path)
    for host in json_data['hosts']:
        assert host['facts'][0]['facts']['system_purpose_role'] == 'test-role'
        assert host['facts'][0]['facts']['system_purpose_sla'] == 'Self-Support'
        assert host['facts'][0]['facts']['system_purpose_usage'] == 'test-usage'


@pytest.mark.stubbed
def test_rhcloud_inventory_auto_upload_setting():
    """Verify that Automatic inventory upload setting works as expected.

    :id: 0475aaaf-c228-45af-b80c-21d459f62ecb

    :customerscenario: true

    :Steps:
        1. Register a content host with satellite.
        2. Enable "Automatic inventory upload" setting.
        3. Verify that satellite automatically generate and upload
            inventory report once a day.
        4. Disable "Automatic inventory upload" setting.
        5. Verify that satellite is not automatically generating and uploading
            inventory report.

    :expectedresults:
        1. If "Automatic inventory upload" setting is enabled then satellite
        automatically generate and upload inventory report.
        2. If "Automatic inventory upload" setting is disable then satellite
        does not generate and upload inventory report automatically.

    :BZ: 1793017

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_inventory_upload_with_http_proxy():
    """Verify that inventory report generate and upload process finish
    successfully when satellite is using http proxy listening on port 80.

    :id: 310a0c91-e313-474d-a5c6-64e85cea4e12

    :customerscenario: true

    :Steps:
        1. Create a http proxy which is using port 80.
        2. Register a content host with satellite.
        3. Set Default HTTP Proxy setting.
        4. Generate and upload inventory report.
        5. Assert that host is listed in the inventory report.
        6. Assert that upload process finished successfully.

    :expectedresults:
        1. Inventory report generate and upload process finished successfully.
        2. Host is present in the inventory report.

    :BZ: 1936906

    :CaseAutomation: ManualOnly
    """


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_include_parameter_tags_setting(
    inventory_settings, organization_ak_setup, rhcloud_registered_hosts, rhcloud_sat_host
):
    """Verify that include_parameter_tags setting doesn't cause invalid report
    to be generated.

    :id: 3136a1e3-f844-416b-8334-75b27fd9e3a1

    :Steps:
        1. Enable include_parameter_tags setting.
        2. Register a content host with satellite.
        3. Generate inventory report.
        4. Assert that generated report contains valid json file.

    :expectedresults:
        1. Valid json report is created.
        2. satellite_parameter values are string.

    :BZ: 1981869, 1967438

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    virtual_host, baremetal_host = rhcloud_registered_hosts
    local_report_path = robottelo_tmp_dir.joinpath(f'{gen_alphanumeric()}_{org.id}.tar.xz')
    rhcloud_sat_host.update_setting('include_parameter_tags', True)
    generate_inventory_report(rhcloud_sat_host, org)
    # Download report
    rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_download_report(
        destination=local_report_path
    )
    json_data = get_report_data(local_report_path)
    common_assertion(local_report_path)
    for host in json_data['hosts']:
        for tag in host['tags']:
            if tag['namespace'] == 'satellite_parameter':
                assert type(tag['value']) is str
                break


@pytest.mark.tier3
def test_rh_cloud_tag_values(
    inventory_settings, organization_ak_setup, rhcloud_sat_host, rhcloud_registered_hosts
):
    """Verify that tag values are escaped properly when hostgroup name
        contains " (double quote) in it.

    :id: ea7cd7ca-4157-4aac-ad8e-e66b88740ce3

    :customerscenario: true

    :Steps:
        1. Create Hostcollection with name containing double quotes.
        2. Register a content host with satellite.
        3. Add a content host to hostgroup.
        4. Generate inventory report.
        5. Assert that generated report contains valid json file.
        6. Assert that hostcollection tag value is escaped properly.

    :expectedresults:
        1. Valid json report is created.
        2. Tag value is escaped properly.

    :BZ: 1874587, 1874619

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup

    host_col_name = gen_string('alpha')
    host_name = rhcloud_registered_hosts[0].hostname
    host = rhcloud_sat_host.api.Host().search(query={'search': host_name})[0]
    host_collection = rhcloud_sat_host.api.HostCollection(
        organization=org, name=f'"{host_col_name}"', host=[host]
    ).create()

    assert len(host_collection.host) == 1
    local_report_path = robottelo_tmp_dir.joinpath(f'{gen_alphanumeric()}_{org.id}.tar.xz')
    # Generate report
    generate_inventory_report(rhcloud_sat_host, org)
    rhcloud_sat_host.api.Organization(id=org.id).rh_cloud_download_report(
        destination=local_report_path
    )
    common_assertion(local_report_path)
    json_data = get_report_data(local_report_path)
    for host in json_data['hosts']:
        if host['fqdn'] == host_name:
            for tag in host['tags']:
                if tag['key'] == 'host_collection':
                    assert tag['value'] == f'"{host_col_name}"'
                    break
