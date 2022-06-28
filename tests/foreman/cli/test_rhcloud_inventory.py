"""CLI tests for RH Cloud - Inventory, aka Insights Inventory Upload

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
from wait_for import wait_for

from robottelo.config import robottelo_tmp_dir
from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_remote_report_checksum

inventory_sync_task = 'InventorySync::Async::InventoryFullSync'


@pytest.mark.tier3
def test_positive_inventory_generate_upload_cli(
    organization_ak_setup, rhcloud_registered_hosts, rhcloud_sat_host
):
    """Tests Insights inventory generation and upload via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: f2da9506-97d4-4d1c-b373-9f71a52b8ab8

    :customerscenario: true

    :Steps:

        0. Create a VM and register to insights within org having manifest.
        1. Generate and upload report for all organizations
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate_upload
        2. Generate and upload report for specific organization
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate_upload
        3. Generate report for specific organization (don't upload)
            # export organization_id=1
            # export target=/var/lib/foreman/red_hat_inventory/generated_reports/
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate
        4. Upload previously generated report
            (needs to be named 'report_for_#{organization_id}.tar.gz')
            # export organization_id=1
            # export target=/var/lib/foreman/red_hat_inventory/generated_reports/
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:upload

    :expectedresults: Inventory is generated and uploaded to cloud.redhat.com.

    :BZ: 1957129, 1895953, 1956190

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    org, _ = organization_ak_setup
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:report:generate_upload'
    upload_success_msg = f"Generated and uploaded inventory report for organization '{org.name}'"
    result = rhcloud_sat_host.execute(cmd)
    assert result.status == 0
    assert upload_success_msg in result.stdout

    local_report_path = robottelo_tmp_dir.joinpath(f'report_for_{org.id}.tar.xz')
    remote_report_path = (
        f'/var/lib/foreman/red_hat_inventory/uploads/done/report_for_{org.id}.tar.xz'
    )
    wait_for(
        lambda: rhcloud_sat_host.get(remote_path=remote_report_path, local_path=local_report_path),
        timeout=60,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    local_file_data = get_local_file_data(local_report_path)
    assert local_file_data['checksum'] == get_remote_report_checksum(rhcloud_sat_host, org.id)
    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


@pytest.mark.tier3
def test_positive_inventory_recommendation_sync(
    organization_ak_setup,
    rhcloud_registered_hosts,
    rhcloud_sat_host,
):
    """Tests Insights recommendation sync via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 361af91d-1246-4308-9cc8-66beada7d651

    :Steps:

        0. Create a VM and register to insights within org having manifest.
        1. Sync insights recommendation using following foreman-rake command.
            # /usr/sbin/foreman-rake rh_cloud_insights:sync

    :expectedresults: Insights recommendations are successfully synced for the host.

    :BZ: 1957186

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    org, ak = organization_ak_setup
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_insights:sync'
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    result = rhcloud_sat_host.execute(cmd)
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
    assert result.status == 0
    assert result.stdout == 'Synchronized Insights hosts hits data\n'


@pytest.mark.tier3
def test_positive_sync_inventory_status(
    organization_ak_setup,
    rhcloud_registered_hosts,
    rhcloud_sat_host,
):
    """Sync inventory status via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 915ffbfd-c2e6-4296-9d69-f3f9a0e79b32

    :Steps:

        0. Create a VM and register to insights within org having manifest.
        1. Sync inventory status for specific organization.
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:sync

    :expectedresults: Inventory status is successfully synced for satellite hosts.

    :BZ: 1957186

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    org, ak = organization_ak_setup
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:sync'
    success_msg = f"Synchronized inventory for organization '{org.name}'"
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    result = rhcloud_sat_host.execute(cmd)
    assert result.status == 0
    assert success_msg in result.stdout
    # Check task details
    wait_for(
        lambda: rhcloud_sat_host.api.ForemanTask()
        .search(query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    task_output = rhcloud_sat_host.api.ForemanTask().search(
        query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'}
    )
    assert task_output[0].output['host_statuses']['sync'] == 2
    assert task_output[0].output['host_statuses']['disconnect'] == 0


@pytest.mark.stubbed
def test_max_org_size_variable():
    """Verify that if organization had more hosts than specified by max_org_size variable
        then report won't be uploaded.

    :id: 7dd964c3-fde8-4335-ab13-02329119d7f6

    :Steps:

        1. Register few content hosts with satellite.
        2. Change value of max_org_size for testing purpose(See BZ#1962694#c2).
        3. Start report generation and upload using
            ForemanInventoryUpload::Async::GenerateAllReportsJob.perform_now

    :expectedresults: If organization had more hosts than specified by max_org_size variable
        then report won't be uploaded.

    :CaseImportance: Low

    :BZ: 1962694

    :CaseAutomation: ManualOnly

    :CaseLevel: System
    """


@pytest.mark.stubbed
def test_satellite_inventory_slice_variable():
    """Test SATELLITE_INVENTORY_SLICE_SIZE dynflow environment variable.

    :id: ffbef1c7-08f3-444b-9255-2251d5594fcb

    :Steps:

        1. Register few content hosts with satellite.
        2. Set SATELLITE_INVENTORY_SLICE_SIZE=1 dynflow environment variable.
            See BZ#1945661#c1
        3. Run "satellite-maintain service restart --only dynflow-sidekiq@worker-1"
        4. Generate inventory report.

    :expectedresults: Generated report had slice containing only one host.

    :CaseImportance: Low

    :BZ: 1945661

    :CaseAutomation: ManualOnly

    :CaseLevel: System
    """


@pytest.mark.stubbed
def test_rhcloud_external_links():
    """Verify that all external links on Insights and Inventory page are working.

    :id: bc7f6354-ed3e-4ac5-939d-90bfe4177043

    :Steps:

        1. Go to Configure > Inventory upload
        2. Go to Configure > Insights

    :expectedresults: all external links on Insights and Inventory page are working.

    :CaseImportance: Low

    :BZ: 1975093

    :CaseAutomation: ManualOnly

    :CaseLevel: System
    """
