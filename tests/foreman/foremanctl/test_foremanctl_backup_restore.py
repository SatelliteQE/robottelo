"""Tests for foremanctl backup and restore functionality

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

import re

from fauxfactory import gen_string
import pytest

from robottelo.config import settings

pytestmark = [pytest.mark.foremanctl]

BACKUP_DIR = '/tmp/'
BACKUP_PREFIX = 'backup-'
BASIC_FILES = {'foremanctl-state.tar.gz', 'metadata.yml', 'config.snar'}
SAT_FILES = {'candlepin.dump', 'foreman.dump', 'pulp.dump'} | BASIC_FILES
CONTENT_FILES = {'pulp-content.tar.gz', 'pulp.snar'}


@pytest.fixture(autouse=True)
def cleanup_backup_dir(target_sat):
    """Clean up backup directories before and after each test."""
    target_sat.execute(f'rm -rf {BACKUP_DIR}{BACKUP_PREFIX}*')
    yield
    target_sat.execute(f'rm -rf {BACKUP_DIR}{BACKUP_PREFIX}*')


def _assert_backup_files(server, backup_dir, skip_pulp=False):
    """Verify that backup directory contains all expected files.

    :param server: Satellite or Capsule server instance to execute commands on
    :param backup_dir: Path to the backup directory
    :param skip_pulp: Whether pulp content was skipped in the backup
    """
    expected_files = SAT_FILES
    if not skip_pulp:
        expected_files = expected_files | CONTENT_FILES

    ls_output = server.execute(f'ls -a {backup_dir}').stdout
    files = ls_output.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]
    assert set(files).issuperset(expected_files), (
        f'Some required backup files are missing. Expected: {expected_files}, Found: {files}'
    )


def _create_backup(sat, subdir, skip_pulp=False, base_backup=None):
    """Run foremanctl backup and return the timestamped backup subdirectory path."""
    cmd = f'foremanctl backup {subdir} --wait-for-tasks'
    if skip_pulp:
        cmd += ' --skip-pulp-content'
    if base_backup:
        cmd += f' --base-backup {base_backup}'
    result = sat.execute(cmd, timeout='30m')
    assert result.status == 0, f'foremanctl backup failed:\n{result.stdout}\n{result.stderr}'
    location = re.search(r'Location:\s*(\S+)', result.stdout)
    assert location, f'Backup location not found in output:\n{result.stdout}'
    return location.group(1)


def test_positive_offline_backup(module_target_sat):
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
    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir)

    _assert_backup_files(module_target_sat, backup_dir)

    result = module_target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'foremanctl health check failed after backup:\n{result.stdout}'


@pytest.mark.destructive
@pytest.mark.e2e
@pytest.mark.parametrize('skip_pulp', [False, True], ids=['include_pulp', 'skip_pulp'])
def test_positive_backup_restore(module_target_sat, module_synced_repos, skip_pulp):
    """Verify foremanctl restore recovers a satellite to its original state from backup

    :id: cb8447fb-b25f-4ec7-b515-8fe7391bd867

    :parametrized: yes

    :steps:
        1. Create a backup using foremanctl backup (with or without pulp content)
        2. Verify backup contains expected files
        3. Mutate content: add a new repo and delete the existing custom repo
        4. Remove pulp artifacts to confirm restore repopulates them (if pulp included)
        5. Run foremanctl restore with --force flag
        6. Verify restore completes successfully
        7. Run foremanctl health check
        8. Verify pre-backup content (custom and RH repos) is restored
        9. Verify content added after backup is absent
        10. Verify pulp artifacts were restored (if pulp included)

    :expectedresults:
        1. Backup succeeds and contains expected files
        2. Restore completes with exit status 0
        3. Health check passes after restore
        4. Deleted content is restored to original state
        5. Content added after backup is absent
        6. Pulp artifacts are restored (if pulp included)

    :Verifies: SAT-44898
    """
    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir, skip_pulp=skip_pulp)

    _assert_backup_files(module_target_sat, backup_dir, skip_pulp=skip_pulp)

    post_backup_repo = module_target_sat.api.Repository(
        url=settings.repos.yum_3.url, product=module_synced_repos['custom'].product
    ).create()
    post_backup_repo.sync()
    post_backup_repo = post_backup_repo.read()

    deleted_repo_id = module_synced_repos['custom'].id
    deleted_repo_name = module_synced_repos['custom'].name
    module_target_sat.api.Repository(id=deleted_repo_id).delete()
    result = module_target_sat.api.Repository().search(
        query={'search': f'name="{deleted_repo_name}"'}
    )
    assert len(result) == 0, 'Custom repo should be deleted before restore'

    if not skip_pulp:
        module_target_sat.execute('rm -rf /var/lib/pulp/media/artifact')
        assert (
            int(
                module_target_sat.execute(
                    'find /var/lib/pulp/media/artifact -type f | wc -l'
                ).stdout
            )
            == 0
        ), 'Pulp artifacts should be removed before restore'

    result = module_target_sat.execute(
        f'foremanctl restore {backup_dir} --force',
        timeout='30m',
    )
    assert result.status == 0, f'foremanctl restore failed:\n{result.stdout}\n{result.stderr}'

    result = module_target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'foremanctl health check failed after restore:\n{result.stdout}'

    repo = module_target_sat.api.Repository().search(
        query={'search': f'name="{deleted_repo_name}"'}
    )[0]
    assert repo.id == deleted_repo_id, 'Deleted custom repo should be restored'

    rh_repo = module_target_sat.api.Repository().search(
        query={'search': f'''name="{module_synced_repos['rh'].name}"'''}
    )[0]
    assert rh_repo.id == module_synced_repos['rh'].id

    result = module_target_sat.api.Repository().search(
        query={'search': f'name="{post_backup_repo.name}"'}
    )
    assert len(result) == 0, 'Content created after backup should not exist after restore'

    if not skip_pulp:
        assert (
            int(
                module_target_sat.execute(
                    'find /var/lib/pulp/media/artifact -type f | wc -l'
                ).stdout
            )
            > 0
        ), 'Pulp artifacts should be repopulated after restore'


def test_positive_restore_validate(module_target_sat):
    """Verify foremanctl restore --validate checks backup integrity without making changes

    :id: b4573263-ce88-4a89-9600-8e8b89aa3d63

    :steps:
        1. Create a backup using foremanctl backup
        2. Capture system state before validate (health check and services)
        3. Run foremanctl restore with --validate flag
        4. Verify validation completes successfully
        5. Verify system state is unchanged after validate

    :expectedresults:
        1. Backup succeeds
        2. Restore --validate exits with status 0
        3. System health and services remain unchanged after validate

    :Verifies: SAT-44898
    """
    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir)

    health_before = module_target_sat.execute('foremanctl health', timeout='5m')
    assert health_before.status == 0, 'Health check failed before validate'

    result = module_target_sat.execute(
        f'foremanctl restore {backup_dir} --validate',
        timeout='5m',
    )
    assert result.status == 0, (
        f'foremanctl restore --validate failed:\n{result.stdout}\n{result.stderr}'
    )

    health_after = module_target_sat.execute('foremanctl health', timeout='5m')
    assert health_after.status == 0, f'Health check failed after validate:\n{health_after.stdout}'


def test_negative_restore_baddir(module_target_sat):
    """Verify foremanctl restore fails with a non-existing backup directory

    :id: a7b530e6-7496-45b6-ba14-198980dc3ca8

    :steps:
        1. Run foremanctl restore with a non-existing backup directory

    :expectedresults:
        1. Restore command exits with non-zero status

    :Verifies: SAT-44898
    """
    bad_dir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'

    result = module_target_sat.execute(
        f'foremanctl restore {bad_dir} --force',
        timeout='5m',
    )
    assert result.status != 0, 'foremanctl restore should fail with non-existing backup directory'


def test_negative_restore_no_force(module_target_sat):
    """Verify foremanctl restore fails without --force on an existing deployment

    :id: ba844ee3-6837-4f8d-b856-3bd8cf5f1d2a

    :steps:
        1. Create a backup using foremanctl backup
        2. Run foremanctl restore without --force flag

    :expectedresults:
        1. Backup succeeds
        2. Restore command exits with non-zero status due to safety check

    :Verifies: SAT-44898
    """
    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir)

    result = module_target_sat.execute(
        f'foremanctl restore {backup_dir}',
        timeout='5m',
    )
    assert result.status != 0, (
        'foremanctl restore should fail without --force on existing deployment'
    )


@pytest.mark.destructive
@pytest.mark.e2e
def test_positive_backup_restore_incremental(target_sat, function_product):
    """Incremental backup/restore end-to-end test using foremanctl.

    :id: 2fc57857-bba0-425e-a7f2-e70ff5cafaab

    :steps:
        1. Sync a custom repository
        2. Take an initial backup with foremanctl
        3. Create additional content (sync another repo)
        4. Take an incremental backup referencing the initial one
        5. Verify expected files are present in the incremental backup
        6. Restore the initial backup and check system health
        7. Verify the additional content is missing
        8. Restore the incremental backup and check system health
        9. Verify all content is restored

    :expectedresults:
        1. Initial and incremental backups succeed
        2. Expected files are present in the incremental backup
        3. Restore of both backups succeeds
        4. System health checks pass after each restore
        5. Content is present/absent as expected after each restore
    """
    initial_repo = target_sat.api.Repository(
        url=settings.repos.yum_1.url, product=function_product
    ).create()
    initial_repo.sync()
    initial_repo = initial_repo.read()

    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    init_backup_dir = _create_backup(target_sat, subdir)

    secondary_repo = target_sat.api.Repository(
        url=settings.repos.yum_3.url, product=function_product
    ).create()
    secondary_repo.sync()
    secondary_repo = secondary_repo.read()

    inc_backup_dir = _create_backup(target_sat, subdir, base_backup=init_backup_dir)

    _assert_backup_files(target_sat, inc_backup_dir)

    result = target_sat.execute(
        f'foremanctl restore {init_backup_dir} --force',
        timeout='30m',
    )
    assert result.status == 0, f'Initial restore failed:\n{result.stdout}\n{result.stderr}'

    result = target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'Health check failed after initial restore:\n{result.stdout}'

    result = target_sat.api.Repository().search(query={'search': f'name="{secondary_repo.name}"'})
    assert len(result) == 0, 'Secondary repo should not exist after restoring initial backup'

    result = target_sat.execute(
        f'foremanctl restore {inc_backup_dir} --force',
        timeout='30m',
    )
    assert result.status == 0, f'Incremental restore failed:\n{result.stdout}\n{result.stderr}'

    result = target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'Health check failed after incremental restore:\n{result.stdout}'

    repo = target_sat.api.Repository().search(query={'search': f'name="{initial_repo.name}"'})[0]
    assert repo.id == initial_repo.id

    repo = target_sat.api.Repository().search(query={'search': f'name="{secondary_repo.name}"'})[0]
    assert repo.id == secondary_repo.id


def test_negative_backup_incremental_nodir_baddir(target_sat):
    """Try to take an incremental backup with missing or non-existing previous backup path.

    :id: 715a0b22-6b9d-4f0b-b8c3-1ea0713ee68f

    :steps:
        1. Run foremanctl backup with --base-backup but no path argument
        2. Run foremanctl backup with --base-backup pointing to a non-existing directory

    :expectedresults:
        1. Both commands fail with a non-zero exit code
        2. The no-directory variant mentions expected one argument
        3. The bad-directory variant mentions the directory does not exist
        4. No backup directory was created on the filesystem
    """
    subdir = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'

    # No directory: --base-backup without a path
    result = target_sat.execute(f'foremanctl backup {subdir} --base-backup')
    assert result.status != 0, (
        f'Incremental backup without path should have failed:\n{result.stdout}'
    )
    assert '--base-backup: expected one argument' in result.stderr, (
        f'Expected --base-backup argument error, got:\n{result.stderr}'
    )

    # Bad directory: --base-backup with a non-existing path
    nonexistent = f'{BACKUP_DIR}{BACKUP_PREFIX}{gen_string("alpha")}'
    result = target_sat.execute(f'foremanctl backup {subdir} --base-backup {nonexistent}')
    assert result.status != 0, f'Incremental backup should have failed:\n{result.stdout}'
    assert (
        f'Previous backup directory does not exist or is not a valid foremanctl backup: {nonexistent}'
        in result.stdout
    ), f'Expected error referencing bad path {nonexistent}, got:\n{result.stdout}'

    # Verify no backup was created
    result = target_sat.execute(f'test -d {subdir}')
    assert result.status != 0, f'Backup directory {subdir} should not exist after failed backups'
