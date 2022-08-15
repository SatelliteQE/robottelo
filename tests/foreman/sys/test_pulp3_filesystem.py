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


@pytest.mark.upgrade
def test_selinux_status(target_sat):
    """Test SELinux status.

    :id: 43218070-ac5e-4679-b74a-3e2bcb497a0a

    :expectedresults: SELinux is enabled and there are no denials
    """
    # check SELinux is enabled
    result = target_sat.execute('getenforce')
    assert 'Enforcing' in result.stdout
    # check there are no SELinux denials
    result = target_sat.execute('ausearch --input-logs -m avc -ts today --raw')
    assert result.status == 1


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
def test_pulp_directory_exists(target_sat, directory):
    """Check Pulp3 directories are present.

    :id: 96a64932-9e89-4063-9d5b-55c811375361

    :parametrized: yes

    :expectedresults: Directories are present
    """
    # check pulp3 directories present
    assert target_sat.execute(f'test -d {directory}').status == 0, f'{directory} must exist.'


@pytest.mark.upgrade
def test_pulp_service_definitions(target_sat):
    """Test systemd settings for Pulp3 file system layout.

    :id: e584faea-dede-4895-8d7f-411cb074f6c0

    :expectedresults: systemd files are present
    """
    # check pulpcore settings
    result = target_sat.execute('systemctl cat pulpcore-content.socket')
    assert result.status == 0
    assert 'ListenStream=/run/pulpcore-content.sock' in result.stdout
    result = target_sat.execute('systemctl cat pulpcore-content.service')
    assert result.status == 0
    assert 'Requires=pulpcore-content.socket' in result.stdout
    result = target_sat.execute('systemctl cat pulpcore-api.service')
    assert result.status == 0
    assert 'Requires=pulpcore-api.socket' in result.stdout
    # check pulp3 configuration file present
    result = target_sat.execute('test -f /etc/pulp/settings.py')
    assert result.status == 0


@pytest.mark.tier1
def test_pulp_workers_status(target_sat):
    """Ensure pulpcore-workers are in active (running) state

    :BZ: 1848111

    :id: f0b8b354-1a30-41c3-93d7-fb51e99c82b6

    :customerscenario: true

    :expectedresults: Pulpcore-workers are in active (running) state
    """
    output = target_sat.execute('systemctl status pulpcore-worker* | grep Active')
    result = output.stdout.rstrip().splitlines()
    assert all('Active: active (running)' in r for r in result)
