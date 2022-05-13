from urllib.parse import urlparse

import pytest

from robottelo.config import settings
from robottelo.hosts import SatelliteHostError


@pytest.fixture
def foreman_service_teardown(satellite_host):
    """stop and restart of foreman service"""
    yield satellite_host
    satellite_host.execute('satellite-maintain service start --only=foreman')


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


@pytest.fixture(scope='session')
def install_cockpit_plugin(session_target_sat):
    session_target_sat.register_to_dogfood()
    session_target_sat.install_cockpit()
    # TODO remove this change when we start using new host detail view
    setting_object = session_target_sat.api.Setting().search(
        query={'search': 'name=host_details_ui'}
    )[0]
    old_value = setting_object.value
    setting_object.value = False
    setting_object.update({'value'})
    yield
    setting_object.value = old_value
    setting_object.update({'value'})


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
