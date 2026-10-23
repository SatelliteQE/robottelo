"""CLI tests for RH Cloud - Inventory, aka Insights Inventory Upload

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

from datetime import UTC, datetime
import json
import time

import pytest
from wait_for import wait_for

from robottelo.config import robottelo_tmp_dir
from robottelo.utils.io import (
    INSIGHTS_REPORTS_DOWNLOAD_DIR,
    done_dir,
    generated_reports_dir,
    get_local_file_data,
    get_remote_report_checksum,
)

inventory_sync_task = 'InventorySync::Async::InventoryFullSync'
generate_report_jobs = 'ForemanInventoryUpload::Async::GenerateAllReportsJob'


@pytest.mark.e2e
def test_positive_inventory_generate_upload_cli(
    rhcloud_manifest_org, rhcloud_registered_hosts, module_target_sat
):
    """Tests Insights inventory generation and upload via hammer CLI.

    :id: f2da9506-97d4-4d1c-b373-9f71a52b8ab8

    :customerscenario: true

    :steps:

        0. Create a VM and register to insights within org having manifest.
        1. Generate and upload report for specific organization using hammer CLI:
            # hammer insights inventory generate-report --organization-id=1
        2. Wait for the report generation task to complete.
        3. Download the report using hammer CLI:
            # hammer insights inventory download-report --organization-id=1 --path <dir>
        4. Verify the downloaded report content.

    :expectedresults:
        1. Report generation task completes successfully.
        2. Report is generated and uploaded to cloud.redhat.com.
        3. Report can be downloaded successfully using hammer CLI.
        4. Downloaded report file is accessible and contains valid host data.

    :BZ: 1957129, 1895953, 1956190

    :CaseAutomation: Automated
    """
    org = rhcloud_manifest_org
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')

    # Use hammer CLI to generate and upload report
    result = module_target_sat.cli.Insights.inventory_generate_report({'organization-id': org.id})
    success_msg = "Report generation started successfully"
    assert success_msg in result

    # Wait for report generation to complete
    generate_job_name = 'ForemanInventoryUpload::Async::HostInventoryReportJob'
    wait_for(
        lambda: (
            module_target_sat.api.ForemanTask()
            .search(query={'search': f'{generate_job_name} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success'
        ),
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )

    # Download report using hammer CLI instead of accessing the filesystem directly
    local_report_path = robottelo_tmp_dir.joinpath(f'report_for_{org.id}.tar.xz')
    module_target_sat.execute(f'mkdir -p {INSIGHTS_REPORTS_DOWNLOAD_DIR}')

    module_target_sat.cli.Insights.inventory_download_report(
        {'organization-id': org.id, 'path': INSIGHTS_REPORTS_DOWNLOAD_DIR}
    )

    remote_report_path = f'{INSIGHTS_REPORTS_DOWNLOAD_DIR}/report_for_{org.id}.tar.xz'
    module_target_sat.get(remote_path=str(remote_report_path), local_path=str(local_report_path))
    local_file_data = get_local_file_data(local_report_path)

    # Verify checksum using the reusable function
    assert local_file_data['checksum'] == get_remote_report_checksum(
        module_target_sat, remote_report_path
    )
    assert local_file_data['size'] > 0
    assert local_file_data['extractable']
    assert local_file_data['json_files_parsable']

    slices_in_metadata = set(local_file_data['metadata_counts'].keys())
    slices_in_tar = set(local_file_data['slices_counts'].keys())
    assert slices_in_metadata == slices_in_tar
    for slice_name, hosts_count in local_file_data['metadata_counts'].items():
        assert hosts_count == local_file_data['slices_counts'][slice_name]


def test_positive_sync_inventory_status_missing_host_ip(
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
):
    """Sync inventory status via hammer CLI with missing IP.

    :id: 372c03df-038b-49fb-a509-bb28edf178f3

    :steps:

        1. Create a vm and register to insights within org having manifest.
        2. Remove IP from host using foreman-rake console.
        3. Sync inventory status for specific organization using hammer CLI:
            # hammer insights inventory sync --organization-id=1
        4. Wait for sync task to complete.
        5. Verify sync task output shows correct host status counts.

    :expectedresults: Inventory status is successfully synced for satellite host with missing IP.

    :Verifies: SAT-24805

    :customerscenario: true
    """
    org = rhcloud_manifest_org
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    rhcloud_host = module_target_sat.cli.Host.info({'name': rhcloud_registered_hosts[0].hostname})[
        'id'
    ]
    update_ip = module_target_sat.execute(
        f'echo "Host.find({rhcloud_host}).update(ip: nil)" |  foreman-rake console'
    )
    assert 'true' in update_ip.stdout

    # Use hammer CLI to sync inventory status
    result = module_target_sat.cli.Insights.inventory_sync({'organization-id': org.id})
    success_msg = "Inventory sync task started successfully"
    assert success_msg in result
    # Check task details
    wait_for(
        lambda: (
            module_target_sat.api.ForemanTask()
            .search(
                query={
                    'search': f'{inventory_sync_task} and started_at >= "{timestamp}"',
                    'per_page': 'all',
                }
            )[0]
            .result
            == 'success'
        ),
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    task_output = module_target_sat.api.ForemanTask().search(
        query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'}
    )
    host_status = None
    for task in task_output:
        if task.input.get("organization_ids") is None:
            continue
        if str(task.input.get("organization_ids")[0]) == str(org.id):
            host_status = task.output
            break
    assert host_status['host_statuses']['sync'] == 2
    assert host_status['host_statuses']['disconnect'] == 0


def test_positive_sync_inventory_status_cli(
    rhcloud_manifest_org,
    module_target_sat,
    rhcloud_registered_hosts,
):
    """Sync inventory status via hammer:

    :id: cb1e883f-04d2-4564-bbcb-6a0087cabef4

    :steps:

        0. Create a VM and register to insights within org having manifest.
        1. Sync inventory status for specific organization.
            # hammer insights inventory sync --organization_id=1

    :expectedresults: Inventory status is successfully synced for satellite hosts.
    """
    org = rhcloud_manifest_org
    result = module_target_sat.cli.Insights.inventory_sync({'organization-id': org.id})
    success_msg = "Inventory sync task started successfully"
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')

    assert success_msg in result
    # Check task details
    wait_for(
        lambda: (
            module_target_sat.api.ForemanTask()
            .search(query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success'
        ),
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    task_output = module_target_sat.api.ForemanTask().search(
        query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'}
    )
    assert task_output[0].output['host_statuses']['sync'] == 2
    assert task_output[0].output['host_statuses']['disconnect'] == 0


@pytest.mark.stubbed
def test_max_org_size_variable():
    """Verify that if organization had more hosts than specified by max_org_size variable
        then report won't be uploaded.

    :id: 7dd964c3-fde8-4335-ab13-02329119d7f6

    :steps:

        1. Register few content hosts with satellite.
        2. Change value of max_org_size for testing purpose(See BZ#1962694#c2).
        3. Start report generation and upload using
            ForemanTasks.sync_task(ForemanInventoryUpload::Async::GenerateAllReportsJob)

    :expectedresults: If organization had more hosts than specified by max_org_size variable
        then report won't be uploaded.

    :CaseImportance: Low

    :BZ: 1962694

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_satellite_inventory_slice_variable():
    """Test SATELLITE_INVENTORY_SLICE_SIZE dynflow environment variable.

    :id: ffbef1c7-08f3-444b-9255-2251d5594fcb

    :steps:

        1. Register few content hosts with satellite.
        2. Set SATELLITE_INVENTORY_SLICE_SIZE=1 dynflow environment variable.
            See BZ#1945661#c1
        3. Run "satellite-maintain service restart --only dynflow-sidekiq@worker-1"
        4. Generate inventory report.

    :expectedresults: Generated report had slice containing only one host.

    :CaseImportance: Low

    :BZ: 1945661

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
def test_rhcloud_external_links():
    """Verify that all external links on Insights and Inventory page are working.

    :id: bc7f6354-ed3e-4ac5-939d-90bfe4177043

    :steps:

        1. Go to Configure > Inventory upload
        2. Go to Configure > Insights

    :expectedresults: all external links on Insights and Inventory page are working.

    :CaseImportance: Low

    :BZ: 1975093

    :CaseAutomation: ManualOnly
    """


def test_positive_generate_all_reports_job(target_sat):
    """Generate all reports job via foreman-rake console:

    :id: a9e4bfdb-6d7c-4f8c-ae57-a81442926dd8

    :steps:
        1. Disable the Automatic Inventory upload setting.
        2. Execute Foreman GenerateAllReportsJob via foreman-rake.

    :expectedresults: Reports generation works as expected.

    :BZ: 2110163

    :customerscenario: true

    :CaseAutomation: Automated
    """
    try:
        target_sat.update_setting('allow_auto_inventory_upload', False)
        with target_sat.session.shell() as sh:
            # On foremanctl, foreman-rake is a wrapper that rejects tasks not on its allowlist.
            # ALLOW_UNSUPPORTED=true lets it through. The var is harmless on satellite-installer.
            sh.send('foreman-rake console')
            time.sleep(30)  # sleep to allow time for console to open
            sh.send(f'ForemanTasks.async_task({generate_report_jobs})')
            time.sleep(3)  # sleep for the cmd execution
        timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
        wait_for(
            lambda: (
                target_sat.api.ForemanTask()
                .search(
                    query={'search': f'{generate_report_jobs} and started_at >= "{timestamp}"'}
                )[0]
                .result
                == 'success'
            ),
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        task_output = target_sat.api.ForemanTask().search(
            query={'search': f'{generate_report_jobs} and started_at >= {timestamp}'}
        )
        assert task_output[0].result == "success"
    finally:
        target_sat.update_setting('allow_auto_inventory_upload', True)


def test_positive_generate_reports_job_cli(
    rhcloud_manifest_org, module_target_sat, rhcloud_registered_hosts
):
    """Generate reports job via cli:

    :id: 2f3e2e38-fd76-45b0-bf75-07fc12e5a118

    :steps:
        1. Execute hammer insights inventory generate-report.
        2. Download the report using hammer CLI to verify it was uploaded.

    :expectedresults: Report generation succeeds and report can be downloaded successfully.

    :Verifies: SAT-38836
    """
    org = rhcloud_manifest_org

    # Clean up any existing downloaded reports
    module_target_sat.execute(f'rm -rf {INSIGHTS_REPORTS_DOWNLOAD_DIR}')
    module_target_sat.execute(f'mkdir -p {INSIGHTS_REPORTS_DOWNLOAD_DIR}')

    generate_report(org, module_target_sat, disconnected=False)

    # Verify report was uploaded by downloading it via hammer CLI
    module_target_sat.cli.Insights.inventory_download_report(
        {'organization-id': org.id, 'path': INSIGHTS_REPORTS_DOWNLOAD_DIR}
    )

    # Verify the downloaded file exists
    remote_report_path = f'{INSIGHTS_REPORTS_DOWNLOAD_DIR}/report_for_{org.id}.tar.xz'
    check_result = module_target_sat.execute(f'test -f {remote_report_path} && echo "exists"')
    assert check_result.status == 0, (
        f"Downloaded report file not found at {remote_report_path}. "
        f"This indicates the report was not uploaded successfully."
    )
    assert 'exists' in check_result.stdout


def test_positive_generate_reports_job_cli_disconnected(
    rhcloud_manifest_org,
    module_target_sat,
    rhcloud_registered_hosts,
):
    """Generate reports job via cli with --no-upload flag:

    :id: 7540edce-1d4e-4a67-adb6-116729e9bfeb

    :steps:
        1. Execute hammer insights inventory generate-report with --no-upload flag.
        2. Try to download the report using hammer CLI to verify it was NOT uploaded.

    :expectedresults: Report is generated but not uploaded (stays in generated_reports/).

    :Verifies: SAT-38836
    """
    org = rhcloud_manifest_org
    # Clean up any existing reports for this organization to ensure clean state
    module_target_sat.execute(f'rm -f {done_dir}/report_for_{org.id}.tar.xz')
    module_target_sat.execute(f'rm -f {generated_reports_dir}/report_for_{org.id}.tar.xz')

    generate_report(org, module_target_sat, disconnected=True)

    # Check report exists in generated_reports/
    result = module_target_sat.execute(
        f'find {generated_reports_dir} -name "report_for_{org.id}.tar.xz" -type f'
    )
    assert result.status == 0, (
        f"Failed to search for report in {generated_reports_dir}: {result.stderr}"
    )
    assert f'report_for_{org.id}.tar.xz' in result.stdout, (
        f"Report not found in {generated_reports_dir}. "
        f"This indicates the report was not generated with --no-upload."
    )

    # Verify report does NOT exist in done/ folder
    result = module_target_sat.execute(
        f'test -f {done_dir}/report_for_{org.id}.tar.xz && echo "exists" || echo "not found"'
    )
    assert 'not found' in result.stdout, (
        f"Report should not be in {done_dir} when using --no-upload flag"
    )


@pytest.mark.rhel_ver_match('N-2')
def test_positive_download_reports_job_cli_disconnected(
    rhcloud_manifest_org, module_target_sat, rhcloud_registered_hosts
):
    """Download generated report job via cli:

    :id: a9e4bfdb-6d7c-4f8c-ae57-a81442926ddc

    :steps:
        1. Generate a report
        2. Execute hammer insights inventory download-report.

    :expectedresults: Reports download works as expected.

    :Verifies: SAT-41462
    """
    org = rhcloud_manifest_org
    generate_report(org, module_target_sat, disconnected=True)
    report_path = f'/tmp/report_for_{org.id}.tar.xz'
    result = module_target_sat.cli.Insights.inventory_download_report(
        {
            'organization-id': org.id,
            'path': "/tmp",
        }
    )
    time.sleep(5)
    success_msg = f"The response has been saved to {report_path}"
    assert success_msg in result
    command = f'''rm -rf /tmp/report && \
mkdir -p /tmp/report && \
tar xf /tmp/report_for_{org.id}.tar.xz --directory /tmp/report && \
cat $(ls /tmp/report/*.json | grep -v meta)'''

    result = module_target_sat.execute(command)
    assert result.status == 0
    report_data = json.loads(result.stdout)
    assert len(report_data['hosts']) >= len(rhcloud_registered_hosts)


@pytest.mark.rhel_ver_match('N-2')
def test_positive_register_insights_client_host(module_target_sat, rhel_insights_vm):
    """Check the below command executed successfully
    command - insights-client --ansible-host=foo.example.com

    :id: b578371e-ec36-42de-83fa-bcea6e027fe2

    :setup:
        1. Enable, sync RHEL BaseOS and AppStream repositories
        2. Create CV, Publish/promote and create AK for host registration
        3. Register host to satellite, Setup Insights is Yes (Override), Install insights-client

    :steps:
        2. Test connection of insights client
        3. execute insight client command given in the description

    :expectedresults: Command executed successfully

    :Verifies: SAT-28695

    :customerscenario: true

    :CaseAutomation: Automated

    """
    # Test connection of insights client
    assert rhel_insights_vm.execute('insights-client --test-connection').status == 0

    # Execute insight client command
    output = rhel_insights_vm.execute(f'insights-client --ansible-host={rhel_insights_vm.hostname}')
    assert output.status == 0
    assert 'Ansible hostname updated' in output.stdout


def test_positive_check_report_autosync_setting(target_sat):
    """Verify that the Insights report autosync setting is enabled by default.

    :id: 137dffe6-50a4-4327-8e93-79e128bee63b

    :steps:
        1. Check the Insights report autosync setting.

    :expectedresults:
        1. The Insights setting "Synchronize recommendations Automatically" should have value "true"

    :Verifies: SAT-30227
    """
    assert (
        target_sat.cli.Settings.list({'search': 'Synchronize recommendations Automatically'})[0][
            'value'
        ]
        == 'true'
    ), 'Setting is not enabled by default!'


def generate_report(rhcloud_manifest_org, module_target_sat, disconnected=False):
    """Download generated report job via cli"""
    org = rhcloud_manifest_org
    params = {'organization-id': org.id}
    if disconnected:
        params['no-upload'] = True

    result = module_target_sat.cli.Insights.inventory_generate_report(params)
    success_msg = "Report generation started successfully"
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    assert success_msg in result
    # Check task details
    generate_job_name = 'ForemanInventoryUpload::Async::HostInventoryReportJob'
    wait_for(
        lambda: (
            module_target_sat.api.ForemanTask()
            .search(query={'search': f'{generate_job_name} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success'
        ),
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    task_output = module_target_sat.api.ForemanTask().search(
        query={'search': f'{generate_job_name} and started_at >= "{timestamp}"'}
    )
    assert task_output[0].result == "success"
