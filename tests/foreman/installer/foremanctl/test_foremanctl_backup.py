"""Tests for foremanctl backup functionality

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

import re

from fauxfactory import gen_string
import pytest

from robottelo.hosts import Satellite

pytestmark = [pytest.mark.foremanctl]

BACKUP_DIR = '/tmp/'
IOP_FILES = {
    'iop_inventory.dump',
    'iop_vmaas.dump',
    'iop_advisor.dump',
    'iop_remediations.dump',
    'iop_vulnerability.dump',
}
BASIC_FILES = {'config_files.tar.gz', '.config.snar', 'metadata.yml'}
SAT_FILES = {'candlepin.dump', 'foreman.dump', 'pulpcore.dump'} | BASIC_FILES
CAPS_FILES = {'pulpcore.dump'} | BASIC_FILES
CONTENT_FILES = {'pulp_data.tar', '.pulp.snar'}


def get_exp_files(module_target_sat, skip_pulp=False):
    expected_files = SAT_FILES if type(module_target_sat) is Satellite else CAPS_FILES
    if not skip_pulp:
        expected_files = expected_files | CONTENT_FILES
    # IoP support will come when it is supported in CI
    # if type(module_target_sat) is Satellite:
    #    expected_files = expected_files | IOP_FILES if module_target_sat.iop_enabled else expected_files
    return expected_files


def test_positive_offline_backup(module_target_sat, setup_backup_tests):
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
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'

    # Run backup with --wait-for-tasks to ensure no running tasks block it
    result = module_target_sat.execute(
        f'foremanctl backup {subdir} --wait-for-tasks',
        timeout='30m',
    )
    assert result.status == 0, f'foremanctl backup failed:\n{result.stdout}\n{result.stderr}'

    # Verify backup directory was created
    result = module_target_sat.execute(f'test -d {subdir}')
    assert result.status == 0, f'Backup directory {subdir} was not created'

    # Get list of files in backup directory
    # result = module_target_sat.execute(f'ls -a {backup_dir}')
    # assert result.status == 0
    # files = set(result.stdout.split())
    files = module_target_sat.execute(f'ls -a {subdir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]
    expected_files = get_exp_files(module_target_sat)

    # Verify all expected files are present
    assert set(files).issuperset(expected_files), (
        f'Some required backup files are missing. Expected: {expected_files}, Found: {files}'
    )

    # Verify foremanctl is still healthy after backup
    result = module_target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'foremanctl health check failed after backup:\n{result.stdout}'
