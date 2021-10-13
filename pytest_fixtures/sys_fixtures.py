import json
from tempfile import mkstemp

import pytest
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo import ssh
from robottelo.config import settings
from robottelo.errors import GCECertNotFoundError


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


@pytest.fixture(scope='session')
def gce_cert():
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    ssh.upload_file(gce_cert_file, settings.gce.cert_path)
    if ssh.command(f'[ -f {settings.gce.cert_path} ]').return_code != 0:
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
