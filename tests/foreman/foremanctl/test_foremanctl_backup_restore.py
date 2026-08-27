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
BASIC_FILES = {'foremanctl-state.tar.gz', 'metadata.yml'}
SAT_FILES = {'candlepin.dump', 'foreman.dump', 'pulp.dump'} | BASIC_FILES
CONTENT_FILES = {'pulp-content.tar.gz'}


def get_exp_files(module_target_sat, skip_pulp=False):
    expected_files = SAT_FILES
    if not skip_pulp:
        expected_files = expected_files | CONTENT_FILES
    return expected_files


def _create_backup(sat, subdir, skip_pulp=False):
    """Run foremanctl backup and return the timestamped backup subdirectory path."""
    cmd = f'foremanctl backup {subdir} --wait-for-tasks'
    if skip_pulp:
        cmd += ' --skip-pulp-content'
    result = sat.execute(cmd, timeout='30m')
    assert result.status == 0, f'foremanctl backup failed:\n{result.stdout}\n{result.stderr}'
    result = sat.execute(f'test -d {subdir}')
    assert result.status == 0, f'Backup directory {subdir} was not created'
    backup_dir = re.findall(rf'{subdir}/foreman-backup-\S+', result.stdout)
    if not backup_dir:
        ls_result = sat.execute(f'ls -d {subdir}/foreman-backup-*')
        assert ls_result.status == 0, f'No foreman-backup-* subdirectory found in {subdir}'
        backup_dir = ls_result.stdout.strip().splitlines()
    return backup_dir[0]


def _get_backup_dir(sat, subdir):
    """Return the timestamped foreman-backup-* subdirectory created under ``subdir``."""
    result = sat.execute(f'ls -d {subdir}/foreman-backup-*')
    assert result.status == 0, f'No foreman-backup-* subdirectory found in {subdir}'
    return result.stdout.strip().splitlines()[0]


@pytest.mark.destructive
def test_positive_capsule_backup_restore(
    module_target_sat, module_capsule_configured, setup_backup_tests
):
    """Verify foremanctl can backup and restore capsule (smart proxy) data
    from the Satellite using the --target-host option

    :id: 8fc00792-313d-41a8-9dfb-40a2fc200b5d

    :steps:
        1. Configure a smart proxy (capsule)
        2. Run foremanctl backup <dir> --target-host proxy from the Satellite
        3. Verify the backup command completes and the backup directory is created
        4. Run foremanctl restore <backup_dir> --target-host proxy --force
        5. Verify the restore command completes successfully
        6. Verify the capsule is healthy after restore

    :expectedresults:
        1. Backup command exits with status 0 and creates a backup directory
        2. Restore command exits with status 0
        3. Capsule remains healthy after restore

    :Verifies: SAT-45029
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'

    # Backup capsule data from the Satellite via --target-host
    result = module_target_sat.execute(
        f'foremanctl backup {subdir} --target-host proxy',
        timeout='30m',
    )
    assert result.status == 0, (
        f'foremanctl capsule backup failed:\n{result.stdout}\n{result.stderr}'
    )

    # Verify the backup directory was created
    result = module_target_sat.execute(f'test -d {subdir}')
    assert result.status == 0, f'Backup directory {subdir} was not created'
    backup_dir = _get_backup_dir(module_target_sat, subdir)

    # Restore the capsule data from the backup via --target-host
    result = module_target_sat.execute(
        f'foremanctl restore {backup_dir} --target-host proxy --force',
        timeout='30m',
    )
    assert result.status == 0, (
        f'foremanctl capsule restore failed:\n{result.stdout}\n{result.stderr}'
    )

    # Verify the capsule is healthy after restore
    result = module_capsule_configured.execute('foremanctl health', timeout='5m')
    assert result.status == 0, (
        f'foremanctl health check failed on capsule after restore:\n{result.stdout}'
    )


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
    files = module_target_sat.execute(f'ls -a {subdir}/*').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]
    expected_files = get_exp_files(module_target_sat)

    # Verify all expected files are present
    assert set(files).issuperset(expected_files), (
        f'Some required backup files are missing. Expected: {expected_files}, Found: {files}'
    )

    # Verify foremanctl is still healthy after backup
    result = module_target_sat.execute('foremanctl health', timeout='5m')
    assert result.status == 0, f'foremanctl health check failed after backup:\n{result.stdout}'


@pytest.mark.destructive
@pytest.mark.e2e
@pytest.mark.parametrize('skip_pulp', [False, True], ids=['include_pulp', 'skip_pulp'])
def test_positive_backup_restore(
    module_target_sat, setup_backup_tests, module_synced_repos, skip_pulp
):
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
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir, skip_pulp=skip_pulp)

    files = module_target_sat.execute(f'ls {backup_dir}').stdout.split('\n')
    files = [i for i in files if i.strip()]
    expected_files = get_exp_files(module_target_sat, skip_pulp)
    assert set(files).issuperset(expected_files), (
        f'Some required backup files are missing. Expected: {expected_files}, Found: {files}'
    )

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


def test_positive_restore_validate(module_target_sat, setup_backup_tests):
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
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
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


def test_negative_restore_baddir(module_target_sat, setup_backup_tests):
    """Verify foremanctl restore fails with a non-existing backup directory

    :id: a7b530e6-7496-45b6-ba14-198980dc3ca8

    :steps:
        1. Run foremanctl restore with a non-existing backup directory

    :expectedresults:
        1. Restore command exits with non-zero status

    :Verifies: SAT-44898
    """
    bad_dir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'

    result = module_target_sat.execute(
        f'foremanctl restore {bad_dir} --force',
        timeout='5m',
    )
    assert result.status != 0, 'foremanctl restore should fail with non-existing backup directory'


def test_negative_restore_no_force(module_target_sat, setup_backup_tests):
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
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    backup_dir = _create_backup(module_target_sat, subdir)

    result = module_target_sat.execute(
        f'foremanctl restore {backup_dir}',
        timeout='5m',
    )
    assert result.status != 0, (
        'foremanctl restore should fail without --force on existing deployment'
    )
