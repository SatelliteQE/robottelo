"""CLI tests for RH Cloud - Inventory, aka Insights Inventory Upload

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.config import robottelo_tmp_dir
from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_remote_report_checksum


@pytest.mark.tier3
def test_positive_inventory_generate_upload_cli(
    organization_ak_setup, registered_hosts, default_sat
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

    :BZ: 1957129

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    org, _ = organization_ak_setup
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:report:generate_upload'
    upload_success_msg = f"Generated and uploaded inventory report for organization '{org.name}'"
    result = default_sat.execute(cmd)
    assert result.status == 0
    assert upload_success_msg in result.stdout

    local_report_path = robottelo_tmp_dir.joinpath(f'report_for_{org.id}.tar.xz')
    remote_report_path = (
        f'/var/lib/foreman/red_hat_inventory/uploads/done/report_for_{org.id}.tar.xz'
    )
    default_sat.get(remote_path=remote_report_path, local_path=local_report_path)
    local_file_data = get_local_file_data(local_report_path)
    assert local_file_data['checksum'] == get_remote_report_checksum(org.id)
    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


@pytest.mark.stubbed
def test_positive_inventory_recommendation_sync():
    """Tests Insights recommendation sync via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 361af91d-1246-4308-9cc8-66beada7d651

    :Steps:

        0. Create a VM and register to insights within org having manifest.

        1. Sync insights recommendation using following foreman-rake command.
            # /usr/sbin/foreman-rake rh_cloud_insights:sync

    :expectedresults: Insights recommendations are successfully synced for the host.

    :BZ: 1957186

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
def test_positive_sync_inventory_status():
    """Sync inventory status via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 915ffbfd-c2e6-4296-9d69-f3f9a0e79b32

    :Steps:

        0. Create a VM and register to insights within org having manifest.

        1. Sync inventory status for all organizations.
            # /usr/sbin/foreman-rake rh_cloud_inventory:sync

        2. Sync inventory status for specific organization.
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:sync

    :expectedresults: Inventory status is successfully synced for satellite hosts.

    :BZ: 1957186

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
