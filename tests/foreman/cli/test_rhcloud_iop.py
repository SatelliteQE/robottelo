"""CLI tests for IoP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

import pytest
import yaml

from robottelo.config import settings
from robottelo.constants import InstallationServices
from robottelo.enums import InstallMethod
from robottelo.utils.installer import InstallerCommand


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-2')
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

    # Set IPv6 proxy for shell commands
    satellite.enable_ipv6_system_proxy()

    # Satellite + IoP installation with custom certs, based on install method
    if satellite.install_method == InstallMethod.FOREMANCTL:
        # Containerized: deploy Satellite with custom certs via satellitectl, then add the
        # IoP feature with the method-aware helper (foremanctl deploy --add-feature iop).
        satellite.install_satellite_foremanctl(
            parameters=[
                '--certificate-source custom_server',
                f'--certificate-server-certificate /root/{certs_data["cert_file_name"]}',
                f'--certificate-server-key /root/{certs_data["key_file_name"]}',
                f'--certificate-server-ca-certificate /root/{certs_data["ca_bundle_file_name"]}',
            ],
        )
        satellite.configure_iop()
    else:
        # Installer: install the Satellite package and run satellite-installer with custom
        # certs and IoP enabled in a single run.
        iop_settings = settings.rh_cloud.iop

        satellite.download_repofile(
            product='satellite',
            release=settings.server.version.release,
            snap=settings.server.version.snap,
        )
        satellite.register_to_cdn()
        satellite.execute('dnf -y update')
        satellite.install_satellite_or_capsule_package()

        # Set up firewall
        satellite.configure_firewall(
            ports=[
                '53/udp',
                '53/tcp',
                '67/udp',
                '69/udp',
                '80/tcp',
                '443/tcp',
                '5647/tcp',
                '8000/tcp',
                '9090/tcp',
                '8140/tcp',
            ],
        )

        # Set IPv6 proxy for podman to pull images, then log in to the IoP container registry
        satellite.enable_ipv6_podman_proxy()
        satellite.podman_login(
            iop_settings.stage_username, iop_settings.stage_token, iop_settings.stage_registry
        )

        # Set up container image path overrides
        custom_hiera_yaml = yaml.dump(satellite.get_iop_image_paths())
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

    # Assert IoP is enabled
    assert satellite.iop_enabled, 'IoP is not enabled after installation'

    # Assert all services (including IoP) are running (method-aware)
    if satellite.install_method == InstallMethod.INSTALLER:
        result = satellite.execute('hammer ping')
        assert result.stdout.count('Status:') == result.stdout.count(' ok')
        result = satellite.execute('satellite-maintain health check --label services-up -y')
        assert result.status == 0, 'Not all services are running'
    else:
        service_status = satellite.verify_services_running(
            satellite.get_service_names(include_iop=True)
        )
        failed_services = [svc for svc, running in service_status.items() if not running]
        assert not failed_services, f'Services not running: {failed_services}'

    org = satellite.api.Organization().create()
    satellite.upload_manifest(org.id, module_sca_manifest.content)

    cvenv_id = satellite.api_factory.get_cvenv_id(
        org.default_content_view, satellite.api.LifecycleEnvironment(id=org.library.id)
    )
    activation_key = satellite.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=org,
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
    ).create()

    # Host setup

    # Set IPv6 proxy on Content Host for (non-Satellite) dnf repos
    host.enable_ipv6_dnf_proxy()

    host.configure_rex(satellite=satellite, org=org, register=False)
    host.configure_insights_client(
        satellite=satellite,
        activation_key=activation_key,
        org=org,
        rhel_distro=f"rhel{host.os_version.major}",
    )

    # Verify insights-client upload
    result = host.execute('insights-client')
    assert result.status == 0, 'insights-client upload failed'


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-2')
def test_disable_enable_iop(module_satellite_iop, function_sca_manifest, rhel_contenthost):
    """Disable and re-enable IoP on Satellite.

    :id: abe165e1-a3a4-413d-b6aa-5cb51acfeb2e

    :steps:

        1. Install Satellite and IoP
        2. Assert all IoP services are running
        3. Disable IoP by running satellite-installer with `--iop-ensure absent`
        4. Assert all IoP services are stopped, and podman containers, networks, secrets, and volumes are removed
        5. Re-enable IoP with `--iop-ensure present`
        6. Assert all IoP services are running

    :expectedresults: IoP services should be running or absent as configured by the `iop-ensure` installer option

    :CaseAutomation: Automated
    """
    satellite = module_satellite_iop
    host = rhel_contenthost

    # Register the Insights client
    org = satellite.api.Organization().create()
    satellite.upload_manifest(org.id, function_sca_manifest.content)

    cvenv_id = satellite.api_factory.get_cvenv_id(
        org.default_content_view, satellite.api.LifecycleEnvironment(id=org.library.id)
    )
    activation_key = satellite.api.ActivationKey(
        content_view_environment_ids=[cvenv_id],
        organization=org,
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
    ).create()

    host.configure_rex(satellite=satellite, org=org, register=False)
    host.configure_insights_client(
        satellite=satellite,
        activation_key=activation_key,
        org=org,
        rhel_distro=f"rhel{host.os_version.major}",
    )

    result = host.execute('insights-client')
    assert result.status == 0, 'Initial insights-client upload failed'

    # Disable IoP, verify it is stopped, then re-enable it and verify it is running.
    # The service-state verification differs by install method: on a containerized
    # (foremanctl) Satellite the whole product runs as podman containers, so IoP state
    # is checked against podman; on an RPM Satellite it is checked via satellite-maintain.
    if satellite.install_method == InstallMethod.FOREMANCTL:
        # ---------------- Containerized (foremanctl) ----------------
        # Disable IoP
        result = satellite.execute('foremanctl deploy --remove-feature iop', timeout='10m')
        assert result.status == 0, 'Failed to disable IoP'
        assert satellite.restart_services() is True, 'Failed to restart Satellite services'

        # IoP feature is gone and no IoP containers/volumes/secrets/network remain.
        # Core Satellite containers stay up, so each check is scoped to iop-named resources.
        assert not satellite.iop_enabled, 'IoP feature still enabled'

        running = satellite.execute("podman ps --format '{{.Names}}'").stdout
        assert not any(service in running for service in InstallationServices.IOP_SERVICES), (
            'IoP containers still running'
        )

        result = satellite.execute("podman volume ls --filter name=iop --format '{{.Name}}'")
        assert result.stdout.strip() == '', 'IoP podman volumes not removed'

        result = satellite.execute("podman secret ls --filter name=iop --format '{{.Name}}'")
        assert result.stdout.strip() == '', 'IoP podman secrets not removed'

        result = satellite.execute("podman network ls --filter name=iop --format '{{.Name}}'")
        assert result.stdout.strip() == '', 'IoP podman network not removed'

        # Verify the client sees IoP as unavailable, then clean up its registration.
        result = host.execute('insights-client --status')
        assert 'Insights API says this machine is NOT registered.' in result.stdout, (
            'insights-client status check failed'
        )
        result = host.execute('rm -f /etc/insights-client/machine-id; insights-client --register')
        assert result.status == 0, 'Failed to register to Red Hat Lightspeed'
        result = host.execute('insights-client --unregister')
        assert result.status == 0, 'Failed to unregister from Red Hat Lightspeed'

        # Re-enable IoP
        result = satellite.execute('foremanctl deploy --add-feature iop', timeout='10m')
        assert result.status == 0, 'Failed to re-enable IoP'
        assert satellite.restart_services() is True, 'Failed to restart Satellite services'

        # IoP feature is back and all IoP containers are running.
        assert satellite.iop_enabled, 'IoP feature not enabled'
        running = satellite.execute("podman ps --format '{{.Names}}'").stdout
        missing = [svc for svc in InstallationServices.IOP_SERVICES if svc not in running]
        assert not missing, f'IoP containers not running: {missing}'
    else:
        # ---------------- RPM installer ----------------
        # Disable IoP
        command = InstallerCommand(iop_ensure='absent').get_command()
        result = satellite.execute(command, timeout='10m')
        assert result.status == 0, 'Failed to disable IoP'
        assert satellite.restart_services() is True, 'Failed to restart Satellite services'

        # On RPM, podman is used only by IoP, so every podman resource should be gone.
        result = satellite.execute('podman ps -a --noheading')
        assert result.stdout == '', 'Podman containers not removed'

        result = satellite.execute('podman volume ls -n')
        assert result.stdout == '', 'Podman volumes not removed'

        result = satellite.execute('podman secret ls -n')
        assert result.stdout == '', 'Podman secrets not removed'

        result = satellite.execute('podman network ls -n -f "name=iop"')
        assert result.stdout == '', 'Podman network not removed'

        result = satellite.execute('satellite-maintain service status -b')
        assert 'FAIL' not in result.stdout, 'Services not running'
        assert not any(service in result.stdout for service in InstallationServices.IOP_SERVICES), (
            'IoP services not disabled'
        )

        # Verify the client sees IoP as unavailable, then clean up its registration.
        result = host.execute('insights-client --status')
        assert 'Insights API says this machine is NOT registered.' in result.stdout, (
            'insights-client status check failed'
        )
        result = host.execute('rm -f /etc/insights-client/machine-id; insights-client --register')
        assert result.status == 0, 'Failed to register to Red Hat Lightspeed'
        result = host.execute('insights-client --unregister')
        assert result.status == 0, 'Failed to unregister from Red Hat Lightspeed'

        # Re-enable IoP
        command = InstallerCommand(iop_ensure='present').get_command()
        result = satellite.execute(command, timeout='10m')
        assert result.status == 0, 'Failed to re-enable IoP'
        assert satellite.restart_services() is True, 'Failed to restart Satellite services'

        result = satellite.execute('satellite-maintain service status -b')
        assert 'FAIL' not in result.stdout, 'Services not running'
        assert all(service in result.stdout for service in InstallationServices.IOP_SERVICES), (
            'IoP services not enabled'
        )

    # Verify insights-client re-registration and upload against re-enabled IoP.
    result = host.execute('rm -f /etc/insights-client/machine-id; insights-client --register')
    assert result.status == 0, 'Failed to register to IoP'

    result = host.execute('insights-client')
    assert result.status == 0, 'insights-client upload failed'


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-2')
@pytest.mark.parametrize(
    'use_ip',
    [False, True],
    ids=['hostname', 'ip'],
)
@pytest.mark.parametrize(
    'setup_http_proxy',
    [True, False],
    indirect=True,
    ids=['auth_http_proxy', 'unauth_http_proxy'],
)
@pytest.mark.parametrize(
    'module_target_sat_insights',
    [False],
    ids=['local'],
    indirect=True,
)
def test_insights_client_registration_with_http_proxy(
    module_target_sat_insights,
    setup_http_proxy,
    rhel_contenthost,
    activation_key_with_els_manifest_org,
    module_els_manifest_org,
):
    """Verify that insights-client registration works with HTTP Proxy.

    :id: 6ab0842e-9e8b-4d9e-aed4-b183f7e8f44d

    :parametrized: yes

    :setup:
        1. Satellite with Default HTTP Proxy set.

    :steps:
        1. Register a Host with Satellite.
        2. Register host with IoP.
        3. Verify `insights-client --(register|unregister|test-connection|status)`

    :expectedresults:
        1. `insights-client` commands work when Satellite has Default HTTP Proxy set.

    :BZ: 1959932

    :customerscenario: true
    """
    satellite = module_target_sat_insights
    org = module_els_manifest_org

    # Associate the org with the smart proxy so insights/rex registration works (required
    # for IoP, mirroring the rhcloud_manifest_org fixture).
    proxy = satellite.nailgun_smart_proxy.read()
    if org.id not in [proxy_org.id for proxy_org in proxy.organization]:
        proxy.organization = [*proxy.organization, org]
        proxy.update(['organization'])

    # Configure remote execution before registering insights, matching enable_insights().
    rhel_contenthost.configure_rex(satellite=satellite, org=org, register=False)
    rhel_contenthost.configure_insights_client(
        satellite,
        activation_key_with_els_manifest_org,
        org,
        f"rhel{rhel_contenthost.os_version.major}",
    )
    assert rhel_contenthost.execute('insights-client --register').status == 0
    assert rhel_contenthost.execute('insights-client --test-connection').status == 0
    assert rhel_contenthost.execute('insights-client --status').status == 0
    assert rhel_contenthost.execute('insights-client --unregister').status == 0


IOP_CLA_RESPONSE = 'OK'
CLA_QUERY = 'How do I list files in a directory?'


def setup_cla(host, satellite):
    """Install command-line-assistant and configure it to use the Satellite.

    :param host: The registered content host to set up CLA on.
    :param satellite: The Satellite instance whose ``/api/lightspeed`` endpoint is used.
    """
    assert host.execute('dnf install -y command-line-assistant').status == 0, (
        'Failed to install command-line-assistant'
    )
    endpoint = f'https://{satellite.hostname}/api/lightspeed/v1'
    host.execute(
        f"sed -i 's|^endpoint = .*|endpoint = \"{endpoint}\"|' "
        '/etc/xdg/command-line-assistant/config.toml'
    )
    host.execute('systemctl restart clad.service')


def trigger_cla_query(host):
    """Issue a CLA query and return the AI response body.

    The ``c`` command wraps the response in decorative borders (``────…``).
    This function extracts the actual response content between the first
    and last separator lines.

    :param host: The content host with CLA installed.
    :return: The AI response text stripped of decorative framing.
    """
    result = host.execute(f'c "{CLA_QUERY}"', timeout='2m')
    assert result.status == 0, f'CLA query failed: {result.stderr}'
    lines = result.stdout.splitlines()
    separator_indices = [i for i, line in enumerate(lines) if '────' in line]
    if len(separator_indices) >= 2:
        content = '\n'.join(lines[separator_indices[0] + 1 : separator_indices[-1]])
        return content.strip()
    return result.stdout.strip()


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
@pytest.mark.parametrize(
    'module_target_sat_insights',
    [False],
    ids=['local'],
    indirect=True,
)
def test_positive_force_cla_connection_to_cloud_in_iop_mode(
    module_target_sat_insights,
    rhel_insights_vm,
):
    """Verify that Command Line Assistant (CLA/Lightspeed) requests are forwarded to
    the Red Hat cloud even when IoP is enabled, once ``force_cla_connection`` is set.

    Lightspeed is cloud-only: the local IoP gateway does not implement it, so without
    this setting CLA requests would be routed to IoP and fail. When
    ``force_cla_connection`` is enabled, ``/api/lightspeed`` traffic must be forwarded
    to ``https://cert.cloud.redhat.com`` instead.

    :id: cd093169-638b-4327-9a98-50e0a9d973dd

    :setup:
        1. A Satellite with IoP (local Red Hat Lightspeed) enabled.
        2. A RHEL content host registered to the Satellite and Insights.

    :steps:
        1. Enable the ``force_cla_connection`` setting on the Satellite.
        2. Install command-line-assistant on the content host and issue a CLA query
           (proxied through the Satellite's ``/api/lightspeed`` endpoint).
        3. Verify the response is a substantive cloud AI answer (not the IoP fallback).

    :expectedresults:
        The CLA response comes from the cloud (not the IoP fallback).

    :Verifies: SAT-49361

    :parametrized: yes

    """
    satellite = module_target_sat_insights
    host = rhel_insights_vm

    assert satellite.iop_enabled, 'Satellite is not running in IoP mode'

    setup_cla(host, satellite)

    default_value = satellite.update_setting('force_cla_connection', True)
    try:
        response = trigger_cla_query(host)
        assert response != IOP_CLA_RESPONSE, (
            f'CLA response was "{IOP_CLA_RESPONSE}" (IoP fallback); '
            'expected a cloud AI response with force_cla_connection enabled'
        )
    finally:
        satellite.update_setting('force_cla_connection', default_value)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
@pytest.mark.parametrize(
    'module_target_sat_insights',
    [False],
    ids=['local'],
    indirect=True,
)
def test_negative_cla_not_forwarded_to_cloud_in_iop_mode(
    module_target_sat_insights,
    rhel_insights_vm,
):
    """Verify that Command Line Assistant (CLA/Lightspeed) requests are NOT forwarded
    to the Red Hat cloud when IoP is enabled and ``force_cla_connection`` is disabled.

    This is the default IoP behaviour: ``/api/lightspeed`` traffic follows
    ``cert_base_url`` (the local IoP gateway) and must not be routed to the cloud
    unless the admin opts in via ``force_cla_connection``.

    :id: c5efe786-d5f5-4433-b1b0-7b780bbe95a5

    :setup:
        1. A Satellite with IoP (local Red Hat Lightspeed) enabled.
        2. A RHEL content host registered to the Satellite and Insights.

    :steps:
        1. Ensure the ``force_cla_connection`` setting is disabled on the Satellite.
        2. Install command-line-assistant on the content host and issue a CLA query
           (proxied through the Satellite's ``/api/lightspeed`` endpoint).
        3. Verify the response is the IoP fallback (not a cloud AI answer).

    :expectedresults:
        The CLA response is the IoP fallback, not a cloud AI answer.

    :Verifies: SAT-49361

    :parametrized: yes

    """
    satellite = module_target_sat_insights
    host = rhel_insights_vm

    assert satellite.iop_enabled, 'Satellite is not running in IoP mode'

    setup_cla(host, satellite)

    default_value = satellite.update_setting('force_cla_connection', False)
    try:
        response = trigger_cla_query(host)
        assert response == IOP_CLA_RESPONSE, (
            f'CLA response was "{response}"; expected IoP fallback "{IOP_CLA_RESPONSE}" '
            'with force_cla_connection disabled'
        )
    finally:
        satellite.update_setting('force_cla_connection', default_value)


def process_iop_log_options(installer_output):
    """Takes satellite-installer help output as input and returns a dictionary
    with the options as keys and the descriptions of the options as values.
    """
    options_dict = {}
    for line in installer_output.split('\n'):
        parts = line.split()
        if parts:
            option = parts[0]
            description = ' '.join(parts[1:])
            options_dict[option] = description
    return options_dict


def test_set_iop_log_level_via_installer(module_satellite_iop):
    """Set IoP log level to DEBUG using satellite-installer options.

    :id: 0268a6c1-56b5-4a0c-9df9-6c1b34f6cbd7

    :steps:
        1. Run `satellite-installer --full-help` to get the current IoP log levels.
        2. Use satellite-installer to set all IoP log levels to DEBUG.
        3. Use satellite-installer to reset all IoP log levels to defaults.

    :expectedresults:
        1. No IoP log levels are set to DEBUG by default.
        2. All IoP log levels can be set to DEBUG using satellite-installer.
        3. All IoP log levels can be reset to their default values using satellite-installer.

    :Verifies: SAT-41750
    """
    NEW_LOG_LEVEL = 'DEBUG'

    # Retrieve the IoP log level settings from satellite-installer help output
    help_command = InstallerCommand('full-help').get_command()
    log_level_settings = module_satellite_iop.execute(
        f'{help_command} | grep iop.*log-level | grep -v reset'
    ).stdout

    # Process the log level options into a dictionary
    settings_dict = process_iop_log_options(log_level_settings)

    # Verify that no IoP log levels are set to DEBUG by default
    assert NEW_LOG_LEVEL not in settings_dict.values()

    # Use the installer to set all IoP log levels to DEBUG
    command = InstallerCommand(
        iop_core_engine_log_level_insights_core_dr=NEW_LOG_LEVEL,
        iop_core_engine_log_level_insights_kafka_service=NEW_LOG_LEVEL,
        iop_core_engine_log_level_insights_messaging=NEW_LOG_LEVEL,
        iop_core_engine_log_level_root=NEW_LOG_LEVEL,
    ).get_command()
    module_satellite_iop.execute(command)

    # Verify that log levels are now DEBUG
    new_log_level_settings = module_satellite_iop.execute(
        f'{help_command} | grep iop.*log-level | grep -v reset'
    ).stdout
    new_settings_dict = process_iop_log_options(new_log_level_settings)
    for setting in new_settings_dict.values():
        assert 'DEBUG' in setting

    # Ensure log levels are reset to defaults
    command = InstallerCommand(
        'reset-iop-core-engine-log-level-insights-core-dr',
        'reset-iop-core-engine-log-level-insights-kafka-service',
        'reset-iop-core-engine-log-level-insights-messaging',
        'reset-iop-core-engine-log-level-root',
    ).get_command()
    module_satellite_iop.execute(command)
    log_level_settings = module_satellite_iop.execute(
        f'{help_command} | grep iop.*log-level | grep -v reset'
    ).stdout
    settings_dict = process_iop_log_options(log_level_settings)
    assert NEW_LOG_LEVEL not in settings_dict.values()
