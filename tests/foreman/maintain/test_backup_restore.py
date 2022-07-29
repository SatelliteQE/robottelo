"""Test class for satellite-maintain backup and restore functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.logging import logger

pytestmark = pytest.mark.destructive


BACKUP_DIR = "/tmp/"


BASIC_FILES = {"config_files.tar.gz", ".config.snar", "metadata.yml"}
CONTENT_FILES = {"pulp_data.tar", ".pulp.snar"}
OFFLINE_FILES = {"pgsql_data.tar.gz", ".postgres.snar"}
ONLINE_SAT_FILES = {"candlepin.dump", "foreman.dump", "pulpcore.dump", "pg_globals.dump"}
ONLINE_CAPS_FILES = {"pulpcore.dump"}
REMOTE_SAT_FILES = ONLINE_SAT_FILES - {"pg_globals.dump"}


NODIR_MSG = "ERROR: parameter 'BACKUP_DIR': no value provided"
BADDIR_MSG = "The given directory does not contain the required files or has too many files"
NOPREV_MSG = "ERROR: option '--incremental': Previous backup " "directory does not exist"

assert_msg = "Some required backup files are missing"


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_preserve_directory(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup, ensure that '--preserve-directory' option works

    :id: e77dae38-d269-495d-9f48-e9572d2bb5c3

    :steps:
        1. create a backup dir, change owner to postgres
        2. create a backup
        3. check that appropriate files are created in the provided dir

    :expectedresult:
        1. backup succeeds
        2. expected files are stored in the provided dir
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    sat_maintain.execute(f'mkdir {subdir} && chown postgres:postgres {subdir}')

    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'preserve-directory': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    files = sat_maintain.execute(f'ls -a {subdir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = (
            BASIC_FILES | OFFLINE_FILES
            if backup_type == 'offline'
            else BASIC_FILES | ONLINE_SAT_FILES
        )
    assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_split_pulp_tar(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup, ensure that '--split-pulp-tar' option works

    :id: ddc3609d-642f-4161-b7a1-54f4aa069c08

    :setup:
        1. repo with sufficient size synced to the server

    :steps:
        1. create a backup using the split option
        2. check that appropriate files are created
        3. check that pulp_data.tar fits the split size

    :expectedresult:
        1. backup succeeds
        2. expected files are present in the backup
        3. size of the pulp_data.tar smaller than provided value
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    set_size = 100
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'split-pulp-tar': f'{set_size}k'},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = (
            BASIC_FILES | OFFLINE_FILES
            if backup_type == 'offline'
            else BASIC_FILES | ONLINE_SAT_FILES
        )
    assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg

    # Check the split works
    result = sat_maintain.execute(f'du {backup_dir}/pulp_data.tar')
    pulp_tar_size = int(result.stdout.split('\t')[0])
    assert pulp_tar_size <= set_size


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_caspule_features(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup with capsule features as dns, tftp, dhcp, openscap

    :id: 7ebe8fe3-e5c3-454e-8e20-fad0a9d5b464

    :steps:
        1. create a backup
        2. check that appropriate files are created

    :expectedresult:
        1. backup succeeds
        2. expected files are present in the backup
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    features = 'dns,tftp,dhcp,openscap'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'features': features},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = (
            BASIC_FILES | OFFLINE_FILES
            if backup_type == 'offline'
            else BASIC_FILES | ONLINE_SAT_FILES
        )
    assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_all(sat_maintain, setup_backup_tests, module_synced_repos, backup_type):
    """Take a backup with all options provided

    :id: bbaf251f-7764-4b7d-b79b-f5f48f5d3b9e

    :steps:
        1. create an initial backup (for the sake of incremental)
        2. create another backup with all options provided

    :expectedresult:
        1. both backups succeed
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    sat_maintain.execute(f'mkdir -m 0777 {subdir}')
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    init_backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]

    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={
            'assumeyes': True,
            'plaintext': True,
            'force': True,
            'skip-pulp-content': True,
            'preserve-directory': True,
            'split-pulp-tar': '10M',
            'incremental': init_backup_dir,
            'features': 'dns,tfp,dhcp,openscap',
        },
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout


def test_positive_backup_offline_logical(sat_maintain, setup_backup_tests, module_synced_repos):
    """Take an offline backup with '--include-db-dumps' option provided

    :id: dafac83f-75e1-455e-b77f-15fed4eed884

    :steps:
        1. create a backup
        2. check that appropriate files are created

    :expectedresult:
        1. backup succeeds
        2. files for both, offline and online, backup type are created
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type='offline',
        options={'assumeyes': True, 'plaintext': True, 'include-db-dumps': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = BASIC_FILES | OFFLINE_FILES | ONLINE_SAT_FILES
    assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_negative_backup_nodir(sat_maintain, setup_backup_tests, module_synced_repos, backup_type):
    """Try to take a backup not providing a backup path

    :id: f55ff776-d08e-4317-b7a2-073cad91ce59

    :steps:
        1. try to create a backup without path provided

    :expectedresult:
        1. should fail with appropriate error message
    """
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir='',
        backup_type='offline',
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status != 0
    assert NODIR_MSG in str(result.stderr)


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_negative_backup_incremental_nodir(sat_maintain, setup_backup_tests, backup_type):
    """Try to take an incremental backup providing non-existing path to the previous backup
    (expected after --incremental option)

    :id: 4efec2fb-810b-4636-ae26-422a6bcb43cc

    :steps:
        1. try to create an incremental backup with non-existing path provided

    :expectedresult:
        1. should fail with appropriate error message
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir='',
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'incremental': subdir},
    )
    logger.info(result.stdout)
    assert result.status != 0
    assert NOPREV_MSG in str(result.stderr)


def test_negative_restore_nodir(sat_maintain, setup_backup_tests):
    """Try to run restore with no source dir provided

    :id: dadc4e32-c0b8-427f-a449-4ae66fe09268

    :steps:
        1. try to run restore with no path argument provided

    :expectedresult:
        1. should fail with appropriate error message
    """
    result = sat_maintain.cli.Restore.run(
        backup_dir='',
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status != 0
    assert NODIR_MSG in str(result.stderr)


def test_negative_restore_baddir(sat_maintain, setup_backup_tests):
    """Try to run restore with non-existing source dir provided

    :id: 65ccc0d0-ca43-4877-9b29-50037e378ca5

    :steps:
        1. try to run restore with non-existing path provided

    :expectedresult:
        1. should fail with appropriate error message
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Restore.run(
        backup_dir=subdir,
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status != 0
    assert BADDIR_MSG in str(result.stdout)


@pytest.mark.parametrize('skip_pulp', [False, True], ids=['include_pulp', 'skip_pulp'])
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_restore(
    sat_maintain,
    setup_backup_tests,
    module_synced_repos,
    backup_type,
    skip_pulp,
):
    """General backup/restore end-to-end test.

    :id: 4eec7790-b2d5-4aea-83ea-3f0db503e4b9

    :steps:
        1. create a backup of different types
        2. check that appropriate files are created
        3. restore the backup (installer --reset-data is run in this step)
        4. check system health
        5. check the content was restored

    :expectedresult:
        1. backup succeeds
        2. expected files are present in the backup
        3. restore succeeds
        4. system health check succeeds
        5. content is present after restore
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'skip-pulp-content': skip_pulp},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = (
            BASIC_FILES | OFFLINE_FILES
            if backup_type == 'offline'
            else BASIC_FILES | ONLINE_SAT_FILES
        )
    if not skip_pulp:
        assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg
    else:
        assert set(files).issuperset(expected_files), assert_msg

    # Run restore
    if not skip_pulp:
        sat_maintain.execute('rm -rf /var/lib/pulp/media/artifact')
    result = sat_maintain.cli.Restore.run(
        backup_dir=backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )

    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check the system health after restore
    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
    logger.info(result.stdout)
    assert result.status == 0

    # Check that content is present after restore
    repo = sat_maintain.api.Repository().search(
        query={'search': f'''name="{module_synced_repos['custom'].name}"'''}
    )[0]
    assert repo.id == module_synced_repos['custom'].id

    rh_repo = sat_maintain.api.Repository().search(
        query={'search': f'''name="{module_synced_repos['rh'].name}"'''}
    )[0]
    assert rh_repo.id == module_synced_repos['rh'].id

    if not skip_pulp:
        assert int(sat_maintain.run('find /var/lib/pulp/media/artifact -type f | wc -l').stdout) > 0


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_restore_incremental(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Incremental backup/restore end-to-end test.

    :id: 77a66cea-8871-4f90-aba1-5295bfa95ecc

    :steps:
        1. take an initial backup
        2. create additional content
        3. take the incremental backup
        4. check that appropriate files are created
        5. restore initial backup and check system health
        6. check that additional content is missing
        7. restore incremental backup and check system health
        8. check the initial and additional content was restored

    :expectedresults:
        1. initial backup succeeds
        2. incremental backup succeeds
        3. expected files are present in the backup
        4. restore of all backups succeeds
        5. system health check succeeds
        6. content is present after restore
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    init_backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]

    # create additional content
    secondary_repo = sat_maintain.api.Repository(
        url=settings.repos.yum_3.url, product=module_synced_repos['custom'].product
    ).create()
    secondary_repo.sync()
    secondary_repo = secondary_repo.read()

    # take incremental backup
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'incremental': init_backup_dir},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # check for expected files
    inc_backup_dir = re.findall(fr'{subdir}\/satellite-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {inc_backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    if sat_maintain.is_remote_db():
        expected_files = BASIC_FILES | REMOTE_SAT_FILES
    else:
        expected_files = (
            BASIC_FILES | OFFLINE_FILES
            if backup_type == 'offline'
            else BASIC_FILES | ONLINE_SAT_FILES
        )
    assert set(files).issuperset(expected_files | CONTENT_FILES), assert_msg

    # restore initial backup and check system health
    result = sat_maintain.cli.Restore.run(
        backup_dir=init_backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
    logger.info(result.stdout)
    assert result.status == 0

    # check that the additional content is missing at this point
    result = sat_maintain.api.Repository().search(query={'search': f'name="{secondary_repo.name}"'})
    assert len(result) == 0

    # restore incremental backup and check system health
    result = sat_maintain.cli.Restore.run(
        backup_dir=inc_backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    logger.info(result.stdout)
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
    logger.info(result.stdout)
    assert result.status == 0

    # check the initial and additional content was restored
    repo = sat_maintain.api.Repository().search(
        query={'search': f'name="{module_synced_repos["custom"].name}"'}
    )[0]
    assert repo.id == module_synced_repos["custom"].id

    repo = sat_maintain.api.Repository().search(  # noqa
        query={'search': f'name="{secondary_repo.name}"'}
    )[0]
    assert repo.id == secondary_repo.id


@pytest.mark.stubbed
def test_positive_backup_restore_snapshot():
    """Take the snapshot backup of a server, restore it, check for content

    :id: dcf3b815-97ed-4c2e-9f2d-5eedd8591c98

    :setup:
        1. satellite installed on an LVM-based storage with sufficient free extents

    :steps:
        1. create the snapshot backup (with/without pulp)
        2. check that appropriate files are created
        3. restore the backup (installer --reset-data is run in this step)
        4. check system health
        5. check the content was restored

    :expectedresult:
        1. backup succeeds
        2. expected files are present in the backup
        3. restore succeeds
        4. system health check succeeds
        5. content is present after restore

    :CaseAutomation: NotAutomated
    """
