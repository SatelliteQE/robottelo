from urllib.parse import urlparse

import pytest

from robottelo.config import settings
from robottelo.hosts import SatelliteHostError


@pytest.fixture
def foreman_service_teardown(target_sat):
    """stop and restart of foreman service"""
    yield target_sat
    target_sat.execute('satellite-maintain service start')


@pytest.fixture
def allow_repo_discovery(target_sat):
    """Set SELinux boolean to allow Rails to connect to non-standard ports."""
    target_sat.execute('setsebool foreman_rails_can_connect_all on')
    yield
    target_sat.execute('setsebool foreman_rails_can_connect_all off')


@pytest.fixture(autouse=True, scope="session")
def relax_bfa(session_target_sat):
    """Relax BFA protection against failed login attempts"""
    if session_target_sat:
        session_target_sat.cli.Settings.set({'name': 'failed_login_attempts_limit', 'value': '0'})


@pytest.fixture(autouse=True, scope='session')
def proxy_port_range(session_target_sat):
    """Assigns port range for fake_capsules"""
    if session_target_sat:
        port_pool_range = settings.fake_capsules.port_range
        if session_target_sat.execute(f'semanage port -l | grep {port_pool_range}').status != 0:
            session_target_sat.execute(f'semanage port -a -t websm_port_t -p tcp {port_pool_range}')


@pytest.fixture(autouse=False, scope='session')
def puppet_proxy_port_range(session_puppet_enabled_sat):
    """Assigns port range for fake_capsules on puppet_enabled_sat"""
    if session_puppet_enabled_sat:
        port_pool_range = settings.fake_capsules.port_range
        if (
            session_puppet_enabled_sat.execute(f'semanage port -l | grep {port_pool_range}').status
            != 0
        ):
            session_puppet_enabled_sat.execute(
                f'semanage port -a -t websm_port_t -p tcp {port_pool_range}'
            )


@pytest.fixture(scope='class')
def class_cockpit_sat(class_subscribe_satellite):
    class_subscribe_satellite.install_cockpit()
    yield class_subscribe_satellite


@pytest.fixture(scope='module')
def enable_capsule_for_registration(module_target_sat):
    """Enable registration and template features for Satellite internal capsule required for
    global registration command"""
    res = module_target_sat.install(
        cmd_args={},
        cmd_kwargs={'foreman-proxy-registration': 'true', 'foreman-proxy-templates': 'true'},
    )
    assert res.status == 0


@pytest.fixture(scope='session')
def block_fake_repo_access(session_target_sat):
    """Block traffic to given port used by fake repo"""
    repo_server_name = '.'.join(
        urlparse(settings.robottelo.REPOS_HOSTING_URL).netloc.split(':')[:1]
    )
    repo_server_port = '.'.join(
        urlparse(settings.robottelo.REPOS_HOSTING_URL).netloc.split(':')[1:]
    )
    cmd_result = session_target_sat.execute(f'nc -z {repo_server_name} {repo_server_port}')
    if cmd_result.status != 0:
        raise SatelliteHostError(
            f'Error, port {repo_server_name} {repo_server_port} incorrect or already blocked.'
        )
    session_target_sat.execute(
        'firewall-cmd --direct --add-rule ipv4 filter OUTPUT 0 -p tcp -m tcp'
        f' --dport={repo_server_port} -j DROP'
    )
    cmd_result = session_target_sat.execute(f'nc -z {repo_server_name} {repo_server_port}')
    if cmd_result.status != 1:
        raise SatelliteHostError(f'Error, port {repo_server_name} {repo_server_port} not blocked.')
    yield
    session_target_sat.execute(
        'firewall-cmd --direct --remove-rule ipv4 filter OUTPUT 0 -p tcp -m tcp'
        f' --dport={repo_server_port} -j DROP'
    )
