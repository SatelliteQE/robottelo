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
from robottelo.constants import CERT_DATA, InstallationServices
from robottelo.enums import InstallMethod
from robottelo.utils.installer import InstallerCommand

IOP_SERVICES = InstallationServices.IOP_SERVICES


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
    iop_settings = settings.rh_cloud.iop

    # Satellite + IoP installation

    # Set IPv6 proxy for shell commands
    satellite.enable_ipv6_system_proxy()

    # Install satellite packages
    satellite.download_repofile(
        product='satellite',
        release=settings.server.version.release,
        snap=settings.server.version.snap,
    )
    satellite.register_to_cdn()
    satellite.execute('dnf -y update')
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

    # Set IPv6 proxy for podman to pull images
    satellite.enable_ipv6_podman_proxy()

    # Log in to container registries. The core Satellite images (postgres, foreman,
    # pulp, candlepin) are pulled from the production registry, while the IoP images
    # come from the stage registry, so we need to authenticate to both.
    result = satellite.execute(
        f'podman login --authfile /etc/foreman/registry-auth.json -u {iop_settings.username!r} -p {iop_settings.token!r} {iop_settings.registry}'
    )
    assert result.status == 0, (
        f'Error logging in to container registry {iop_settings.registry}: {result.stdout}'
    )

    result = satellite.execute(
        f'podman login --authfile /etc/foreman/registry-auth.json -u {iop_settings.stage_username!r} -p {iop_settings.stage_token!r} {iop_settings.stage_registry}'
    )
    assert result.status == 0, (
        f'Error logging in to container registry {iop_settings.stage_registry}: {result.stdout}'
    )

    if satellite.install_method == InstallMethod.FOREMANCTL:
        # deploy creates the iop-*.image quadlet files, so it must run before we
        # can override the images they point at.
        result = satellite.execute(
            'foremanctl deploy --flavor satellite --add-feature iop'
            ' --add-feature hammer --add-feature foreman-proxy'
            f' --certificate-source=custom_server'
            f' --certificate-server-certificate /root/{certs_data["cert_file_name"]}'
            f' --certificate-server-key /root/{certs_data["key_file_name"]}'
            f' --certificate-server-ca-certificate /root/{certs_data["ca_bundle_file_name"]}',
            timeout='30m',
        )
        assert result.status == 0, f'Failed to deploy IoP: {result.stdout}'
        # Now the .image files exist, point each at our override image, then reload
        # systemd and restart the units so they re-pull the overridden images.
        for service, image in iop_settings.image_paths.items():
            quadlet_name = f'iop-{service.replace("_", "-")}'
            satellite.execute(
                f"sed -i 's|^Image=.*|Image={image}|' /etc/containers/systemd/{quadlet_name}.image"
            )
        satellite.execute('systemctl daemon-reload')
        result = satellite.execute("systemctl restart 'iop-*'")
    else:
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

    # Assert all services are running. satellite-maintain does not exist on
    # foremanctl, so check the service units directly (works on both methods).
    assert not satellite.get_failed_services(include_iop=True), 'Not all services are running'

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
def test_positive_configure_iop_custom_certs(
    satellite_host,
    module_sca_manifest,
    rhel_contenthost,
):
    """Reconfigure a Satellite to use custom SSL certs and enable IoP.

    :id: 6c7dadc4-f181-4f58-9873-494026acf84f

    :steps:

        1. Generate custom certs on the Satellite
        2. Apply the custom certs to the Satellite
        3. Assert success return code from the cert update
        4. Enable IoP (Red Hat Lightspeed) on the Satellite
        5. Assert all services are running
        6. Register client to Satellite and upload insights-client data
        7. Assert success return code from insights-client

    :expectedresults: Satellite serves the custom certs and IoP is functional.

    :CaseAutomation: Automated
    """
    satellite = satellite_host
    host = rhel_contenthost

    # Set IPv6 proxy for shell commands on the Satellite
    satellite.enable_ipv6_system_proxy()

    # Generate custom certs on the Satellite for its own hostname
    satellite.custom_cert_generate(CERT_DATA['capsule_hostname'])
    server_cert = f'/root/{satellite.hostname}/{satellite.hostname}.crt'
    server_key = f'/root/{satellite.hostname}/{satellite.hostname}.key'
    server_ca_cert = f'/root/{CERT_DATA["ca_bundle_file_name"]}'

    # Apply the custom certs to the already-deployed Satellite. The base Satellite
    # (with its core images) is provisioned by Broker, so we only reconfigure it to
    # serve the custom certs instead of re-running the base install ourselves.
    if satellite.install_method == InstallMethod.FOREMANCTL:
        result = satellite.execute(
            'foremanctl deploy --certificate-source=custom_server'
            f' --certificate-server-certificate {server_cert}'
            f' --certificate-server-key {server_key}'
            f' --certificate-server-ca-certificate {server_ca_cert}',
            timeout='30m',
        )
    else:
        command = InstallerCommand(
            'certs-update-server',
            'certs-update-server-ca',
            certs_server_cert=server_cert,
            certs_server_key=server_key,
            certs_server_ca_cert=server_ca_cert,
        ).get_command()
        result = satellite.execute(command, timeout='30m')
    assert result.status == 0, f'Failed to apply custom certs: {result.stdout}'

    # Enable IoP. configure_iop() handles both install methods and the stage image
    # overrides, and reuses the custom certs already persisted on the Satellite.
    satellite.configure_iop()

    result = satellite.execute('hammer ping')
    assert result.stdout.count('Status:') == result.stdout.count(' ok')

    # Assert all services are running. satellite-maintain does not exist on
    # foremanctl, so check the service units directly (works on both methods).
    assert not satellite.get_failed_services(include_iop=True), 'Not all services are running'

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
def test_disable_enable_iop(module_satellite_iop, module_sca_manifest, rhel_contenthost):
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

    host.configure_rex(satellite=satellite, org=org, register=False)
    host.configure_insights_client(
        satellite=satellite,
        activation_key=activation_key,
        org=org,
        rhel_distro=f"rhel{host.os_version.major}",
    )

    result = host.execute('insights-client')
    assert result.status == 0, 'Initial insights-client upload failed'

    # Disable IoP
    if satellite.install_method == InstallMethod.FOREMANCTL:
        result = satellite.execute('foremanctl deploy --remove-feature iop', timeout='30m')
    else:
        command = InstallerCommand(iop_ensure='absent').get_command()
        result = satellite.execute(command, timeout='10m')
    assert result.status == 0, 'Failed to disable IoP'

    assert satellite.restart_services() is True, 'Failed to restart Satellite services'

    if satellite.install_method == InstallMethod.FOREMANCTL:
        # Core Satellite services run as podman containers too, so only the
        # IoP-specific containers/volumes/secrets should be removed.
        result = satellite.execute('podman ps -a --noheading --filter "name=iop"')
        assert result.stdout == '', 'IoP podman containers not removed'

        result = satellite.execute('podman volume ls -n -f "name=iop"')
        assert result.stdout == '', 'IoP podman volumes not removed'

        result = satellite.execute('podman secret ls -n -f "name=iop"')
        assert result.stdout == '', 'IoP podman secrets not removed'
    else:
        # Only IoP uses podman on installer deployments, so everything is removed.
        result = satellite.execute('podman ps -a --noheading')
        assert result.stdout == '', 'Podman containers not removed'

        result = satellite.execute('podman volume ls -n')
        assert result.stdout == '', 'Podman volumes not removed'

        result = satellite.execute('podman secret ls -n')
        assert result.stdout == '', 'Podman secrets not removed'

    result = satellite.execute('podman network ls -n -f "name=iop"')
    assert result.stdout == '', 'Podman network not removed'

    assert not satellite.get_failed_services(), 'Core Satellite services not running'
    result = satellite.execute('podman ps -a --format "{{.Names}}"')
    assert not any(service in result.stdout for service in IOP_SERVICES), (
        'IoP services not disabled'
    )

    # Verify insights-client re-registration
    result = host.execute('insights-client --status')
    assert 'Insights API says this machine is NOT registered.' in result.stdout, (
        'insights-client status check failed'
    )

    result = host.execute('rm -f /etc/insights-client/machine-id; insights-client --register')
    assert result.status == 0, 'Failed to register to Red Hat Lightspeed'

    result = host.execute('insights-client --unregister')
    assert result.status == 0, 'Failed to unregister from Red Hat Lightspeed'

    # Re-enable IoP
    if satellite.install_method == InstallMethod.FOREMANCTL:
        result = satellite.execute('foremanctl deploy --add-feature iop', timeout='30m')
    else:
        command = InstallerCommand(iop_ensure='present').get_command()
        result = satellite.execute(command, timeout='10m')
    assert result.status == 0, 'Failed to re-enable IoP'

    assert satellite.restart_services() is True, 'Failed to restart Satellite services'

    assert not satellite.get_failed_services(include_iop=True), 'Services not running'

    # Verify insights-client re-registration again
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
    rhel_contenthost.configure_insights_client(
        module_target_sat_insights,
        activation_key_with_els_manifest_org,
        module_els_manifest_org,
        f"rhel{rhel_contenthost.os_version.major}",
    )
    assert rhel_contenthost.execute('insights-client --register').status == 0
    assert rhel_contenthost.execute('insights-client --test-connection').status == 0
    assert rhel_contenthost.execute('insights-client --status').status == 0
    assert rhel_contenthost.execute('insights-client --unregister').status == 0


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


@pytest.mark.foreman_installer
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
