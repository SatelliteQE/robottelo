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
from robottelo.utils.installer import InstallerCommand

IOP_SERVICES = [
    'iop-core-engine',
    'iop-core-gateway',
    'iop-core-host-inventory-api',
    'iop-core-host-inventory-migrate',
    'iop-core-host-inventory',
    'iop-core-ingress',
    'iop-core-kafka',
    'iop-core-puptoo',
    'iop-core-yuptoo',
    'iop-service-advisor-backend-api',
    'iop-service-advisor-backend',
    'iop-service-remediations-api',
    'iop-service-vmaas-reposcan',
    'iop-service-vmaas-webapp-go',
    'iop-service-vuln-dbupgrade',
    'iop-service-vuln-evaluator-recalc',
    'iop-service-vuln-evaluator-upload',
    'iop-service-vuln-grouper',
    'iop-service-vuln-listener',
    'iop-service-vuln-manager',
    'iop-service-vuln-taskomatic',
]


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
@pytest.mark.rhel_ver_match('N-0')
def test_disable_enable_iop(satellite_iop, module_sca_manifest, rhel_contenthost):
    """Install Satellite + IoP, disable, re-enable.

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
    satellite = satellite_iop
    host = rhel_contenthost

    # Register the Insights client
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
    assert result.status == 0, 'Initial insights-client upload failed'

    # Disable IoP
    command = InstallerCommand(iop_ensure='absent').get_command()
    result = satellite.execute(command, timeout='10m')
    assert result.status == 0, 'Failed to disable IoP'

    result = satellite.execute('satellite-maintain service restart')
    assert result.status == 0, 'Failed to restart Satellite services'

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
    command = InstallerCommand(iop_ensure='present').get_command()
    result = satellite.execute(command, timeout='10m')
    assert result.status == 0, 'Failed to re-enable IoP'

    result = satellite.execute('satellite-maintain service restart')
    assert result.status == 0, 'Failed to restart Satellite services'

    result = satellite.execute('satellite-maintain service status -b')
    assert 'FAIL' not in result.stdout, 'Services not running'
    assert all(service in result.stdout for service in IOP_SERVICES), 'IoP services not enabled'

    # Verify insights-client re-registration again
    result = host.execute('rm -f /etc/insights-client/machine-id; insights-client --register')
    assert result.status == 0, 'Failed to register to IoP'

    result = host.execute('insights-client')
    assert result.status == 0, 'insights-client upload failed'
