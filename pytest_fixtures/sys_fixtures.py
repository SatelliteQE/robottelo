import pytest

from robottelo.config import settings
from robottelo.rhsso_utils import run_command
from robottelo.ssh import command as ssh_command


@pytest.fixture
def foreman_service_teardown():
    """stop and restart of foreman service"""
    yield
    run_command('foreman-maintain service start --only=foreman')


@pytest.fixture
def allow_repo_discovery():
    """Set SELinux boolean to allow Rails to connect to non-standard ports."""
    ssh_command('setsebool foreman_rails_can_connect_all on')
    yield
    ssh_command('setsebool foreman_rails_can_connect_all off')


@pytest.fixture(autouse=True, scope="session")
def relax_bfa():
    """Relax BFA protection against failed login attempts

    The robottelo.ssh.command should resolve the hostname for the current xdist worker
    """
    if settings.server.hostname:
        ssh_command(
            f'hammer -u admin -p {settings.server.admin_password} '
            'settings set --name "failed_login_attempts_limit" --value 0'
        )
