import pytest

from robottelo.config import settings
from robottelo.hosts import SatelliteHostError


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
    if default_sat:
        port_pool_range = settings.fake_capsules.port_range
        if default_sat.execute(f'semanage port -l | grep {port_pool_range}').status != 0:
            default_sat.execute(f'semanage port -a -t websm_port_t -p tcp {port_pool_range}')


@pytest.fixture
def register_to_dogfood():
    pass


# TODO install from dogfood, path should be saved in conf/repos and in settings.repos.dogfood
# settings.repos.dogfood_repo_host
# yum -y localinstall <dogfood url>
# TODO register satellite by command register_contenthost
#  with org and activation key from command below
# TODO parametrize it for each satellite version
# subscription-manager register --org <dogfood org> --activationkey <dogfood act-key>
# TODO after registration install cockpit plugin can be started

# TODO BZ needs to be mentioned otherwise I would forget
# instead of  'foreman-maintain packages install -y tfm-rubygem-foreman_remote_execution-cockpit'
# 'foreman-installer --enable-foreman-plugin-remote-execution-cockpit' should be used


@pytest.fixture
def install_cockpit_plugin(default_sat, register_to_dogfood):
    cmd_result = default_sat.execute(
        'foreman-maintain packages install -y tfm-rubygem-foreman_remote_execution-cockpit'
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
        raise SatelliteHostError(f'ssh-copy id finished with error: {cmd_result.stdout}')
