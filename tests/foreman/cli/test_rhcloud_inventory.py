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

from nailgun.entity_mixins import TaskFailedError
import pytest
from wait_for import wait_for
import yaml

from robottelo import constants
from robottelo.config import robottelo_tmp_dir, settings
from robottelo.constants import DEFAULT_CV, DEFAULT_ORG, ENVIRONMENT
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.io import get_local_file_data, get_remote_report_checksum

inventory_sync_task = 'InventorySync::Async::InventoryFullSync'
generate_report_jobs = 'ForemanInventoryUpload::Async::GenerateAllReportsJob'


@pytest.mark.e2e
def test_positive_inventory_generate_upload_cli(
    rhcloud_manifest_org, rhcloud_registered_hosts, module_target_sat
):
    """Tests Insights inventory generation and upload via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: f2da9506-97d4-4d1c-b373-9f71a52b8ab8

    :customerscenario: true

    :steps:

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
    """
    org = rhcloud_manifest_org
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:report:generate_upload'
    upload_success_msg = f"Generated and uploaded inventory report for organization '{org.name}'"
    result = module_target_sat.execute(cmd)
    assert result.status == 0
    assert upload_success_msg in result.stdout

    local_report_path = robottelo_tmp_dir.joinpath(f'report_for_{org.id}.tar.xz')
    remote_report_path = (
        f'/var/lib/foreman/red_hat_inventory/uploads/done/report_for_{org.id}.tar.xz'
    )
    wait_for(
        lambda: module_target_sat.get(
            remote_path=str(remote_report_path), local_path=str(local_report_path)
        ),
        timeout=60,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    local_file_data = get_local_file_data(local_report_path)
    assert local_file_data['checksum'] == get_remote_report_checksum(module_target_sat, org.id)
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
def test_positive_inventory_recommendation_sync(
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
):
    """Tests Insights recommendation sync via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 361af91d-1246-4308-9cc8-66beada7d651

    :steps:

        0. Create a VM and register to insights within org having manifest.
        1. Sync insights recommendation using following foreman-rake command.
            # /usr/sbin/foreman-rake rh_cloud_insights:sync

    :expectedresults: Insights recommendations are successfully synced for the host.

    :BZ: 1957186

    :CaseAutomation: Automated
    """
    org = rhcloud_manifest_org
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_insights:sync'
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    result = module_target_sat.execute(cmd)
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
    assert result.status == 0
    assert 'Synchronized Insights hosts hits data' in result.stdout


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
def test_positive_sync_inventory_status(
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
):
    """Sync inventory status via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: 915ffbfd-c2e6-4296-9d69-f3f9a0e79b32

    :steps:

        0. Create a VM and register to insights within org having manifest.
        1. Sync inventory status for specific organization.
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:sync

    :expectedresults: Inventory status is successfully synced for satellite hosts.

    :BZ: 1957186

    :CaseAutomation: Automated
    """
    org = rhcloud_manifest_org
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:sync'
    success_msg = f"Synchronized inventory for organization '{org.name}'"
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    result = module_target_sat.execute(cmd)
    assert result.status == 0
    assert success_msg in result.stdout
    # Check task details
    wait_for(
        lambda: module_target_sat.api.ForemanTask()
        .search(query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
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


def test_positive_sync_inventory_status_missing_host_ip(
    rhcloud_manifest_org,
    rhcloud_registered_hosts,
    module_target_sat,
):
    """Sync inventory status via foreman-rake commands with missing IP.

    :id: 372c03df-038b-49fb-a509-bb28edf178f3

    :steps:

        1. Create a vm and register to insights within org having manifest.
        2. Remove IP from host.
        3. Sync inventory status for specific organization.
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:sync


    :expectedresults: Inventory status is successfully synced for satellite host with missing IP.

    :Verifies: SAT-24805

    :customerscenario: true
    """
    org = rhcloud_manifest_org
    cmd = f'organization_id={org.id} foreman-rake rh_cloud_inventory:sync'
    success_msg = f"Synchronized inventory for organization '{org.name}'"
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
    rhcloud_host = module_target_sat.cli.Host.info({'name': rhcloud_registered_hosts[0].hostname})[
        'id'
    ]
    update_ip = module_target_sat.execute(
        f'echo "Host.find({rhcloud_host}).update(ip: nil)" | foreman-rake console'
    )
    assert 'true' in update_ip.stdout
    result = module_target_sat.execute(cmd)
    assert result.status == 0
    assert success_msg in result.stdout
    # Check task details
    wait_for(
        lambda: module_target_sat.api.ForemanTask()
        .search(
            query={
                'search': f'{inventory_sync_task} and started_at >= "{timestamp}"',
                'per_page': 'all',
            }
        )[0]
        .result
        == 'success',
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
        lambda: module_target_sat.api.ForemanTask()
        .search(query={'search': f'{inventory_sync_task} and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
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


def test_positive_cloud_connector_enable_cli(module_target_sat):
    """Cloud-connector enable via hammer:

    :id: 7f9e9918-f5b4-48bd-b316-328c3951fa42

    :steps:

        0. Create a VM and register to insights within org having manifest.
        1. Enable cloud connector.
            # hammer insights cloud-connector enable

    :expectedresults: Cloud connector enablement starts successfully.
    """
    result = module_target_sat.cli.Insights.cloud_connector_enable({})
    success_msg = "Cloud connector enable task started"
    assert success_msg in result


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
            sh.send('foreman-rake console')
            time.sleep(30)  # sleep to allow time for console to open
            sh.send(f'ForemanTasks.async_task({generate_report_jobs})')
            time.sleep(3)  # sleep for the cmd execution
        timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M')
        wait_for(
            lambda: target_sat.api.ForemanTask()
            .search(query={'search': f'{generate_report_jobs} and started_at >= "{timestamp}"'})[0]
            .result
            == 'success',
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

    :expectedresults: Reports generation works as expected.
    """
    org = rhcloud_manifest_org
    generate_report(org, module_target_sat, disconnected=False)

    result = module_target_sat.api.Organization(id=org.id).rh_cloud_fetch_last_upload_log()
    expected = 'Connected to cert.cloud.redhat.com'
    assert expected in result['output']


def test_positive_generate_reports_job_cli_disconnected(
    rhcloud_manifest_org,
    module_target_sat,
    rhcloud_registered_hosts,
):
    """Generate reports job via cli:

    :id: 7540edce-1d4e-4a67-adb6-116729e9bfeb

    :steps:
        1. Execute hammer insights inventory generate-report.

    :expectedresults: Reports generation works as expected.

    :BlockedBy: SAT-38836
    """
    org = rhcloud_manifest_org
    generate_report(org, module_target_sat, disconnected=True)

    result = module_target_sat.api.Organization(id=org.id).rh_cloud_fetch_last_upload_log()
    expected = 'Upload canceled because connection to Insights is not enabled or the --no-upload option was passed.'
    assert expected == result['output']


def test_positive_download_reports_job_cli_disconnected(
    rhcloud_manifest_org, module_target_sat, rhcloud_registered_hosts
):
    """Download generated report job via cli:

    :id: a9e4bfdb-6d7c-4f8c-ae57-a81442926ddc

    :steps:
        1. Generate a report
        2. Execute hammer insights inventory download-report.

    :expectedresults: Reports download works as expected.
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
    generate_job_name = 'ForemanInventoryUpload::Async::GenerateReportJob'
    wait_for(
        lambda: module_target_sat.api.ForemanTask()
        .search(query={'search': f'{generate_job_name} and started_at >= "{timestamp}"'})[0]
        .result
        == 'success',
        timeout=400,
        delay=15,
        silent_failure=True,
        handle_exception=True,
    )
    task_output = module_target_sat.api.ForemanTask().search(
        query={'search': f'{generate_job_name} and started_at >= "{timestamp}"'}
    )
    assert task_output[0].result == "success"

    report_log = module_target_sat.api.Organization(id=org.id).rh_cloud_fetch_last_report_log()
    expected = f'Successfully generated /var/lib/foreman/red_hat_inventory/generated_reports/report_for_{org.id}.tar.xz for organization id {org.id}'
    assert expected in report_log['output']


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-0')
def test_positive_install_iop_custom_certs(
    certs_data,
    sat_ready_rhel,
    module_sca_manifest,
    rhel_contenthost,
):
    """Install Satellite + IoP with custom SSL certs.

    :id: 9528fc93-822d-461e-af84-283dfdc0043f

    :steps:

        1. Generate the custom certs on RHEL machine
        2. Install Satellite and IoP with custom certs
        3. Assert success return code from satellite-installer
        4. Assert all services are running
        5. Register client to Satellite and upload insights-client data
        6. Assert success return code from insights-client

    :expectedresults: Satellite should be installed using the custom certs.

    :CaseAutomation: Automated
    """
    satellite = sat_ready_rhel
    host = rhel_contenthost
    iop_settings = settings.rh_cloud.iop_advisor_engine

    # Set IPv6 system proxy on Satellite, to reach container registry
    satellite.enable_ipv6_system_proxy()

    # Set IPv6 dnf proxy on Content Host, to install insights-client from non-Satellite source
    host.enable_ipv6_dnf_proxy()

    # Install satellite packages
    satellite.download_repofile(
        product='satellite',
        release=settings.server.version.release,
        snap=settings.server.version.snap,
    )
    satellite.register_to_cdn()
    satellite.execute('dnf -y update')
    satellite.execute('dnf -y install podman')
    satellite.install_satellite_or_capsule_package()

    # Set up firewall
    result = satellite.execute(
        "which firewall-cmd || dnf -y install firewalld && systemctl enable --now firewalld"
    )
    assert result.status == 0, "firewalld is not present and can't be installed"

    result = satellite.execute(
        'firewall-cmd --add-port="53/udp" --add-port="53/tcp" --add-port="67/udp" '
        '--add-port="69/udp" --add-port="80/tcp" --add-port="443/tcp" '
        '--add-port="5647/tcp" --add-port="8000/tcp" --add-port="9090/tcp" '
        '--add-port="8140/tcp"'
    )
    assert result.status == 0

    result = satellite.execute('firewall-cmd --runtime-to-permanent')
    assert result.status == 0

    # Log in to container registry
    result = satellite.execute(
        f'podman login --authfile /etc/foreman/registry-auth.json -u {iop_settings.stage_username!r} -p {iop_settings.stage_token!r} {iop_settings.stage_registry}'
    )
    assert result.status == 0, f'Error logging in to container registry: {result.stdout}'

    # Set up container image path overrides
    custom_hiera_yaml = yaml.dump(
        {f'iop::{service}::image': path for service, path in iop_settings.image_paths.items()}
    )
    satellite.execute(f'echo "{custom_hiera_yaml}" > /etc/foreman-installer/custom-hiera.yaml')

    command = InstallerCommand(
        'enable-iop',
        'certs-update-server',
        'certs-update-server-ca',
        scenario='satellite',
        certs_server_cert=f'/root/{certs_data["cert_file_name"]}',
        certs_server_key=f'/root/{certs_data["key_file_name"]}',
        certs_server_ca_cert=f'/root/{certs_data["ca_bundle_file_name"]}',
        foreman_initial_admin_password=settings.server.admin_password,
    ).get_command()

    result = satellite.execute(command, timeout='30m')
    assert result.status == 0

    result = satellite.execute('hammer ping')
    assert result.stdout.count('Status:') == result.stdout.count(' ok')

    # Assert all services are running
    result = satellite.execute('satellite-maintain health check --label services-up -y')
    assert result.status == 0, 'Not all services are running'

    org = satellite.api.Organization().create()
    satellite.upload_manifest(org.id, module_sca_manifest.content)

    activation_key = satellite.api.ActivationKey(
        content_view=org.default_content_view,
        organization=org,
        environment=satellite.api.LifecycleEnvironment(id=org.library.id),
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
        auto_attach=False,
    ).create()

    host.configure_rex(satellite=satellite, org=org, register=False)
    host.configure_insights_client(
        satellite=satellite,
        activation_key=activation_key,
        org=org,
        rhel_distro=f"rhel{host.os_version.major}",
    )

    result = host.execute('insights-client')
    assert result.status == 0, 'insights-client upload failed'


def test_positive_config_on_sat_without_network_protocol(target_sat, function_sca_manifest):
    """Test cloud connector configuration on Satellite without explicit network protocol.

    :id: e6bf1c56-3091-4db2-b162-4cf3c6e23394

    :steps:
        1. Get default organization, content view, and lifecycle environment.
        2. Upload manifest to enable Red Hat content.
        3. Enable and sync RHEL BaseOS and AppStream repositories.
        4. Create activation key and register Satellite to itself.
        5. Enable cloud connector via CLI.
        6. Verify that the 'Configure Cloud Connector' job template executes successfully.
        7. Check that rhcd service proxy configuration is properly set.

    :expectedresults:
        1. Satellite is successfully registered.
        2. Cloud connector is enabled successfully.
        3. The job invocation for configuring cloud connector succeeds.
        4. The rhcd.service.d/proxy.conf file contains the correct NO_PROXY environment variable
           with the FQDN without https:// prefix.

    :Verifies: SAT-34224

    :customerscenario: true
    """
    # Get the default organization, content view, and lifecycle environment from Satellite
    org = target_sat.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
    cv = target_sat.api.ContentView().search(query={'search': f'name="{DEFAULT_CV}"'})[0]
    lce = target_sat.api.LifecycleEnvironment().search(query={'search': f'name="{ENVIRONMENT}"'})[0]
    with pytest.raises(TaskFailedError,
                       match="Owner has already imported from another subscription management application"):
        # Upload manifest to enable Red Hat content
        target_sat.upload_manifest(org.id, function_sca_manifest.content)

    # Enable and sync RHEL BaseOS and AppStream repositories based on Satellite's OS version
    rhel_ver = target_sat.os_version.major
    for name in [f'rhel{rhel_ver}_bos', f'rhel{rhel_ver}_aps']:
        # Enable the Red Hat repository and get its ID
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=constants.REPOS[name]['product'],
            repo=constants.REPOS[name]['name'],
            reposet=constants.REPOS[name]['reposet'],
            releasever=constants.REPOS[name]['version'],
        )
        # Sync the repository
        rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
        rh_repo.sync(timeout=2000)

    # Create an activation key for Satellite self-registration
    ac_key = target_sat.api.ActivationKey(
        content_view=cv.id,
        environment=lce.id,
        organization=org,
    ).create()

    # Register the Satellite to itself using the activation key
    result = target_sat.register(org, None, ac_key.name, target_sat, force=False)
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Enable cloud connector
    result = target_sat.cli.Insights.cloud_connector_enable({})
    assert "Cloud connector enable task started" in result

    # Find the job invocation for the 'Configure Cloud Connector' template
    template_name = 'Configure Cloud Connector'
    result = target_sat.api.JobInvocation().search(
        query={'search': f'description="{template_name}"'}
    )[0]

    # Wait for the job to complete
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {result.id}', poll_timeout=600
    )

    # Verify the job completed successfully
    result = target_sat.api.JobInvocation(id=result.id).read()
    assert result.status_label == 'succeeded'

    # Read the rhcd service proxy configuration file to verify correct setup
    status = target_sat.execute('cat /etc/systemd/system/rhcd.service.d/proxy.conf')
    # Check the correct format is present
    assert f'Environment=NO_PROXY={target_sat.hostname}' in status.stdout
    # Ensure NO_PROXY doesn't contain https:// prefix
    assert 'Environment=NO_PROXY=https://' not in status.stdout
