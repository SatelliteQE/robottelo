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
import pytest

from robottelo import ssh
from robottelo.rh_cloud_utils import get_local_file_data
from robottelo.rh_cloud_utils import get_remote_report_checksum


@pytest.mark.tier3
def test_positive_inventory_generate_upload_cli(organization_ak_setup, registered_hosts):
    """Tests Insights inventory generation and upload via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: f2da9506-97d4-4d1c-b373-9f71a52b8ab8

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

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    org, ak = organization_ak_setup
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:report:generate_upload'
    upload_success_msg = f'Generated and uploaded inventory report for organization \'{org.name}\''
    result = ssh.command(cmd)
    assert result.return_code == 0
    assert result.stdout[0] == upload_success_msg

    local_report_path = f'/tmp/report_for_{org.id}.tar.xz'
    remote_report_path = (
        f'/var/lib/foreman/red_hat_inventory/uploads/done/report_for_{org.id}.tar.xz'
    )
    ssh.download_file(remote_report_path, local_report_path)
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
