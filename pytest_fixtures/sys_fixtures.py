import json
from tempfile import mkstemp

import pytest
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.errors import GCECertNotFoundError
from robottelo.hosts import Satellite
from robottelo.hosts import SatelliteHostError


@pytest.fixture
def foreman_service_teardown(satellite_host):
    """stop and restart of foreman service"""
    yield satellite_host
    satellite_host.execute('foreman-maintain service start --only=foreman')


@pytest.fixture
def allow_repo_discovery(default_sat):
    """Set SELinux boolean to allow Rails to connect to non-standard ports."""
    default_sat.execute('setsebool foreman_rails_can_connect_all on')
    yield
    default_sat.execute('setsebool foreman_rails_can_connect_all off')


@pytest.fixture(autouse=True, scope="session")
def relax_bfa(default_sat):
    """Relax BFA protection against failed login attempts"""
    if default_sat:
        default_sat.cli.Settings.set({'name': 'failed_login_attempts_limit', 'value': '0'})


@pytest.fixture(autouse=True, scope='session')
def proxy_port_range(default_sat):
    """Assigns port range for fake_capsules"""
    if default_sat:
        port_pool_range = settings.fake_capsules.port_range
        if default_sat.execute(f'semanage port -l | grep {port_pool_range}').status != 0:
            default_sat.execute(f'semanage port -a -t websm_port_t -p tcp {port_pool_range}')


@pytest.fixture
def register_to_dogfood(default_sat):
    dogfood_canonical_hostname = settings.repos.dogfood_repo_host.partition('//')[2]
    # get hostname of dogfood machine
    dig_result = default_sat.execute(f'dig +short {dogfood_canonical_hostname}')
    # the host name finishes with a dot, so last character is removed
    dogfood_hostname = dig_result.stdout.split()[0][:-1]
    dogfood = Satellite(dogfood_hostname)
    default_sat.install_katello_ca(satellite=dogfood)
    # satellite version consist from x.y.z, we need only x.y
    sat_release = '.'.join(default_sat.version.split('.')[:-1])
    cmd_result = default_sat.register_contenthost(
        org='Sat6-CI', activation_key=f'satellite-{sat_release}-qa-rhel7'
    )
    if cmd_result.status != 0:
        raise SatelliteHostError(f'Error during registration, command output: {cmd_result.stdout}')


@pytest.fixture
def install_cockpit_plugin(default_sat, register_to_dogfood):
    cmd_result = default_sat.execute(
        'foreman-installer --enable-foreman-plugin-remote-execution-cockpit', timeout='30m'
    )
    if cmd_result.status != 0:
        raise SatelliteHostError(
            f'Error during cockpit installation, installation output: {cmd_result.stdout}'
        )
    cmd_result = default_sat.execute(
        f'sshpass -p "{settings.server.ssh_password}" ssh-copy-id \
        -i ~foreman-proxy/.ssh/id_rsa_foreman_proxy -o StrictHostKeyChecking=no localhost'
    )
    if cmd_result.status != 0:
        raise SatelliteHostError(f'Error during ssh-copy-id, command output: {cmd_result.stdout}')


@pytest.fixture(scope='session')
def gce_cert(default_sat):
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    default_sat.put(gce_cert_file, settings.gce.cert_path)
    if default_sat.execute(f'[ -f {settings.gce.cert_path} ]').status != 0:
        raise GCECertNotFoundError(
            f"The GCE certificate in path {settings.gce.cert_path} is not found in satellite."
        )
    return cert


@pytest.fixture(scope='session')
def googleclient(gce_cert):
    gceclient = GoogleCloudSystem(
        project=gce_cert['project_id'],
        zone=settings.gce.zone,
        file_path=gce_cert['local_path'],
        file_type='json',
    )
    yield gceclient
    gceclient.disconnect()
