import pytest

from robottelo.config import settings


@pytest.fixture
def foreman_service_teardown(default_sat):
    """stop and restart of foreman service"""
    yield
    default_sat.execute('foreman-maintain service start --only=foreman')


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
    port_pool_range = settings.fake_capsules.port_range
    if default_sat.execute(f'semanage port -l | grep {port_pool_range}').status != 0:
        default_sat.execute(f'semanage port -a -t websm_port_t -p tcp {port_pool_range}')
        print("Test")
