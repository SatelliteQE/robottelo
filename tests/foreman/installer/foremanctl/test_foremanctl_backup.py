"""Tests for foremanctl backup functionality

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

import pytest


@pytest.mark.foremanctl
def test_positive_offline_backup(foremanctl_sat):
    """Verify foremanctl backup creates a backup successfully

    :id: e9eafa8a-4f1b-458c-b24b-c31d4bc04c4b

    :steps:
        1. Run foremanctl backup with --wait-for-tasks flag
        2. Verify backup command completes successfully
        3. Verify backup directory was created
        4. Verify backup contains expected files (databases, config files, etc.)

    :expectedresults:
        1. Backup command exits with status 0
        2. Backup directory exists
        3. Backup contains database dumps and configuration files

    :Verifies: SAT-44895
    """
    backup_dir = '/var/tmp/foreman-backup-test'

    # Clean up any existing backup directory
    foremanctl_sat.execute(f'rm -rf {backup_dir}')

    # Run backup with --wait-for-tasks to ensure no running tasks block it
    result = foremanctl_sat.execute(
        f'foremanctl backup {backup_dir} --wait-for-tasks',
        timeout='30m',
    )
    assert result.status == 0, f'foremanctl backup failed:\n{result.stdout}\n{result.stderr}'

    # Verify backup directory was created
    result = foremanctl_sat.execute(f'test -d {backup_dir}')
    assert result.status == 0, f'Backup directory {backup_dir} was not created'

    # Verify backup directory contains expected content
    result = foremanctl_sat.execute(f'ls -la {backup_dir}/*')
    assert result.status == 0

    # Database dumps should be present
    result = foremanctl_sat.execute(f'ls {backup_dir}/* | grep .dump').stdout
    assert 'candlepin.dump' in result
    assert 'pulp.dump' in result
    assert 'foreman.dump' in result

    # Verify backup metadata file exists
    result = foremanctl_sat.execute(f'ls {backup_dir}/* | grep metadata.yml').stdout
    assert 'metadata.yml' in result

    # Verify pulp content exists
    result = foremanctl_sat.execute(f'ls {backup_dir}/* | grep pulp-content.tar.gz').stdout
    assert "pulp-content.tar.gz" in result

    # Verify foremanctl is still active
    result = foremanctl_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0
