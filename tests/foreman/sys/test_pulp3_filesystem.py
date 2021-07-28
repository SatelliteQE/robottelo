"""Tests for Pulp3 file system.

:Requirement: Pulp3 installed

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Pulp

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import pytest

from robottelo.ssh import get_connection


@pytest.fixture(scope='session')
def connection(timeout=100):
    with get_connection(timeout=timeout) as connection:
        yield connection


@pytest.mark.upgrade
def test_selinux_status(connection):
    """Test SELinux status.

    :id: 43218070-ac5e-4679-b74a-3e2bcb497a0a

    :expectedresults: SELinux is enabled and there are no denials

    """
    # check SELinux is enabled
    result = connection.run('getenforce')
    assert 'Enforcing' in result.stdout[0]
    # check there are no SELinux denials
    result = connection.run('ausearch --input-logs -m avc -ts today --raw')
    assert result.return_code == 1


@pytest.mark.upgrade
@pytest.mark.parametrize(
    'directory',
    [
        '/var/lib/pulp',
        '/var/lib/pulp/assets',
        '/var/lib/pulp/media',
        '/var/lib/pulp/tmp',
    ],
)
def test_pulp_directory_exists(connection, directory):
    """Check Pulp3 directories are present.

    :id: 96a64932-9e89-4063-9d5b-55c811375361

    :parametrized: yes

    :expectedresults: Directories are present

    """
    # check pulp3 directories present
    assert connection.run(f'test -d {directory}').return_code == 0, f'{directory} must exist.'


@pytest.mark.upgrade
def test_pulp_service_definitions(connection):
    """Test systemd settings for Pulp3 file system layout.

    :id: e584faea-dede-4895-8d7f-411cb074f6c0

    :expectedresults: systemd files are present

    """
    # check pulpcore settings
    result = connection.run('systemctl cat pulpcore-content.socket')
    assert result.return_code == 0
    assert 'ListenStream=/run/pulpcore-content.sock' in result.stdout[3]
    result = connection.run('systemctl cat pulpcore-content.service')
    assert result.return_code == 0
    assert 'Requires=pulpcore-content.socket' in result.stdout[2]
    result = connection.run('systemctl cat pulpcore-api.service')
    assert result.return_code == 0
    assert 'Requires=pulpcore-api.socket' in result.stdout[3]
    # check pulp3 configuration file present
    result = connection.run('test -f /etc/pulp/settings.py')
    assert result.return_code == 0
