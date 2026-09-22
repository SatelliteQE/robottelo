"""Tests For Disconnected Satellite Installation

:Requirement: Installation (disconnected satellite installation)

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: High

"""

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.hosts import Satellite

SATELLITE_FIREWALL_PORTS = [8000, 8443]

pytestmark = [pytest.mark.foremanctl]


def install_satellite_disconnected_iso(
    sat,
    satellite_iso_url,
    rhel_iso_url,
    nogpgcheck=True,
    satellite_mount_point='/mnt/satellite-iso',
    rhel_mount_point='/mnt/rhel-iso',
):
    """Install Satellite in a disconnected network environment from ISO images.

    1. Download the RHEL binary DVD ISO and Satellite ISO while the host still
       has network access.
    2. Disconnect the host from the CDN and container registry.
    3. Mount the RHEL ISO and configure offline BaseOS and AppStream repositories
       from it.
    4. Install podman and skopeo from the offline repositories.
    5. Mount the Satellite ISO and run ``prepare_system`` to install
       satellitectl, copy the ISO content to /opt/satellite, configure the local
       Satellite repository, and import all container images into local storage.
    6. Unmount the Satellite ISO and remove the downloaded ISO file to reclaim
       disk space.
    7. Verify local hostname resolution for satellitectl deploy.
    8. Install and configure firewalld with the ports required by Satellite.
    9. Run ``satellitectl deploy --flavor satellite`` to install the Satellite.

    The RHEL binary DVD ISO provides the base operating system packages. The
    Satellite ISO provides the satellitectl package and, through its
    ``prepare_system`` script, all container images imported into the local
    container storage. ``prepare_system`` needs skopeo present and copies the
    whole ISO content to /opt/satellite, so the host needs a disk fitting both
    ISO images, that copy and the imported container images.

    :param satellite_iso_url: URL of the Satellite ISO image
    :param rhel_iso_url: URL of the RHEL binary DVD ISO image
    :param nogpgcheck: skip GPG signature verification, needed for unsigned composes
    :param satellite_mount_point: directory the Satellite ISO is mounted at
    :param rhel_mount_point: directory the RHEL binary DVD ISO is mounted at
    :return: result of the final satellitectl deploy command
    """
    # Download both ISO images while the host still has network access
    rhel_iso = sat.download_iso(rhel_iso_url)
    satellite_iso = sat.download_iso(satellite_iso_url)

    # Cut the host off and serve the base operating system from the RHEL ISO
    sat.disconnect_from_network()
    sat.mount_iso(rhel_iso, rhel_mount_point)
    sat.setup_offline_rhel_repos(rhel_mount_point)
    # prepare_system verifies the signature of the packages it installs
    sat.execute('rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release')
    assert sat.execute('dnf -y install podman skopeo').status == 0, (
        'Failed to install podman and skopeo from the offline repositories'
    )

    # Install satellitectl and import the container images from the Satellite ISO.
    # prepare_system copies the whole ISO to /opt/satellite, configures a local repo
    # out of it and skopeo-imports every container image into local storage.
    sat.mount_iso(satellite_iso, satellite_mount_point)
    try:
        prepare_system = f'./prepare_system{" --nogpgcheck" if nogpgcheck else ""}'
        result = sat.execute(f'cd {satellite_mount_point} && {prepare_system}', timeout='60m')
        assert result.status == 0, (
            f'prepare_system failed with exit code {result.status}:\n{result.stdout}\n{result.stderr}'
        )
        assert "Please run satellitectl deploy" in result.stdout, (
            f'prepare_system did not finish the installation:\n{result.stdout}'
        )
    finally:
        sat.execute(f'umount {satellite_mount_point}')

    # The ISO content now lives under /opt/satellite, reclaim the space it took
    sat.execute(f'rm -f {satellite_iso}')

    # Verify the FQDN of the host resolves locally
    assert sat.execute('ping -c1 localhost && ping -c1 $(hostname -f)').status == 0, (
        f'The hostname of {sat.hostname} does not resolve'
    )

    # Configure firewall to open communication
    assert (
        sat.execute(
            '(which firewall-cmd || dnf -y install firewalld) && systemctl enable --now firewalld'
        ).status
        == 0
    ), 'firewalld is not present and can\'t be installed'
    firewall_commands = [
        'firewall-cmd --permanent --add-service=http',
        'firewall-cmd --permanent --add-service=https',
        *(f'firewall-cmd --permanent --add-port={port}/tcp' for port in SATELLITE_FIREWALL_PORTS),
        'firewall-cmd --reload',
    ]
    firewall_result = sat.execute(' && '.join(firewall_commands))
    assert firewall_result.status == 0, (
        f'Failed to configure Satellite firewall:\n{firewall_result.stdout}\n{firewall_result.stderr}'
    )

    deploy_parameters = [
        f'--initial-admin-username {settings.server.admin_username}',
        f'--initial-admin-password {settings.server.admin_password}',
    ]
    deploy = sat.execute(
        f'satellitectl deploy --flavor satellite  {" ".join(deploy_parameters)}',
        timeout='60m',
    )
    assert deploy.status == 0, f'satellitectl deploy failed:\n{deploy.stdout}\n{deploy.stderr}'

    return deploy


@pytest.fixture(scope='module')
def module_disconnected_sat():
    """Install a Satellite in a disconnected network environment from ISO images.

    Deploys a bare RHEL host, downloads the RHEL binary DVD ISO and the Satellite
    ISO onto it, cuts the host off from the CDN and the container registry, and
    installs Satellite from the ISO images alone.
    """
    disconnected = settings.server.get('disconnected', {})
    # The Satellite ISO is pulled for the release under test, so that the master branch
    # installs the stream ISO while the 6.20.z branch installs the 6.20 one
    satellite_iso_url = disconnected.get('satellite_iso_url')
    rhel_iso_url = disconnected.get('rhel_iso_url')
    if not all((satellite_iso_url, rhel_iso_url)):
        pytest.skip(
            'Both server.disconnected.satellite_iso_url and server.disconnected.rhel_iso_url '
            'must be set to run the disconnected installation tests'
        )

    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.default,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
        use_dynamic_inventories_wf_level=False,
    ) as sat:
        install_satellite_disconnected_iso(
            sat,
            satellite_iso_url=satellite_iso_url,
            rhel_iso_url=rhel_iso_url,
            nogpgcheck=disconnected.get('nogpgcheck', True),
        )
        # A disconnected Satellite must not try to reach the Red Hat Portal
        sat.cli.Settings.set({'name': 'subscription_connection_enabled', 'value': 'No'})
        yield sat


@pytest.mark.e2e
def test_positive_server_installer_from_iso(module_disconnected_sat):
    """Install Satellite from an ISO image in a disconnected network environment.

    :id: 38c08646-9f71-48d9-a9c2-66bd94c3e5bb

    :setup:
        1. Deploy a bare RHEL host.
        2. Download the RHEL binary DVD ISO and the Satellite ISO onto the host.
        3. Unregister the host from the CDN and drop all repofiles, proxy
           configuration and container registry credentials.
        4. Mount the RHEL ISO and serve BaseOS and AppStream from it.
        5. Mount the Satellite ISO and run its prepare_system script, which
           installs satellitectl and imports all container images locally.
        6. Run satellitectl deploy.

    :steps:
        1. Verify no content source outside the ISO images is configured.
        2. Verify satellitectl health reports a healthy deployment.
        3. Verify the subscription connection is disabled.

    :expectedresults:
        1. Satellite is installed from the local ISO repositories and Satellite ISO.
        2. The deployment is healthy and does not use CDN repositories or portal connection.
    """
    sat = module_disconnected_sat

    # The only enabled repositories are the ones served from the mounted RHEL ISO
    repos = sat.execute('dnf repolist --enabled -q').stdout
    assert 'iso_baseos' in repos, f'Offline BaseOS repository is not enabled:\n{repos}'
    assert 'iso_appstream' in repos, f'Offline AppStream repository is not enabled:\n{repos}'
    assert 'cdn.redhat.com' not in sat.execute('cat /etc/yum.repos.d/*.repo').stdout, (
        'A Red Hat CDN repository is configured on a disconnected Satellite'
    )
    assert sat.execute('subscription-manager identity').status != 0, (
        'A disconnected Satellite must not be registered to the CDN'
    )

    result = sat.execute('satellitectl health', timeout='5m')
    assert result.status == 0, f'satellitectl health failed:\n{result.stdout}\n{result.stderr}'

    # A disconnected Satellite does not talk to the Red Hat Portal
    connection_enabled = sat.cli.Settings.info({'name': 'subscription_connection_enabled'})
    assert connection_enabled['value'].lower() == 'false', (
        f'Subscription connection is still enabled: {connection_enabled["value"]}'
    )
