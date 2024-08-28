"""Test class for satellite-maintain backup and restore functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: High


"""

import re

from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.content_info import get_repo_files_by_url
from robottelo.hosts import Satellite

pytestmark = pytest.mark.destructive


BACKUP_DIR = "/tmp/"


BASIC_FILES = {"config_files.tar.gz", ".config.snar", "metadata.yml"}
SAT_FILES = {"candlepin.dump", "foreman.dump", "pulpcore.dump"} | BASIC_FILES
CAPS_FILES = {"pulpcore.dump"} | BASIC_FILES
CONTENT_FILES = {"pulp_data.tar", ".pulp.snar"}


NODIR_MSG = "ERROR: parameter 'BACKUP_DIR': no value provided"
BADDIR_MSG = "The given directory does not contain the required files or has too many files"
NOPREV_MSG = "ERROR: option '--incremental': Previous backup " "directory does not exist"

assert_msg = "Some required backup files are missing"


def get_exp_files(sat_maintain, skip_pulp=False):
    expected_files = SAT_FILES if type(sat_maintain) is Satellite else CAPS_FILES
    if not skip_pulp:
        expected_files = expected_files | CONTENT_FILES
    return expected_files


def get_instance_name(sat_maintain):
    """Get the instance name depending on target type."""
    return 'satellite' if type(sat_maintain) is Satellite else 'capsule'


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_preserve_directory(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup, ensure that '--preserve-directory' option works

    :id: e77dae38-d269-495d-9f48-e9572d2bb5c3

    :parametrized: yes

    :steps:
        1. create a backup dir, change owner to postgres
        2. create a backup
        3. check that appropriate files are created in the provided dir

    :expectedresults:
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
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    files = sat_maintain.execute(f'ls -a {subdir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain)
    assert set(files).issuperset(expected_files), assert_msg


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_split_pulp_tar(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup, ensure that '--split-pulp-tar' option works

    :id: ddc3609d-642f-4161-b7a1-54f4aa069c08

    :parametrized: yes

    :setup:
        1. repo with sufficient size synced to the server

    :steps:
        1. create a backup using the split option
        2. check that appropriate files are created
        3. check that pulp_data.tar fits the split size

    :expectedresults:
        1. backup succeeds
        2. expected files are present in the backup
        3. size of the pulp_data.tar smaller than provided value

    :customerscenario: true

    :BZ: 2164413
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    instance = get_instance_name(sat_maintain)
    set_size = 100
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'split-pulp-tar': f'{set_size}k'},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain)
    assert set(files).issuperset(expected_files), assert_msg

    # Check the split works
    result = sat_maintain.execute(f'du {backup_dir}/pulp_data.tar')
    pulp_tar_size = int(result.stdout.split('\t')[0])
    assert pulp_tar_size <= set_size


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_capsule_features(
    sat_maintain, setup_backup_tests, module_synced_repos, backup_type
):
    """Take a backup with capsule features as dns, tftp, dhcp, openscap

    :id: 7ebe8fe3-e5c3-454e-8e20-fad0a9d5b464

    :parametrized: yes

    :steps:
        1. create a backup
        2. check that appropriate files are created

    :expectedresults:
        1. backup succeeds
        2. expected files are present in the backup
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    instance = get_instance_name(sat_maintain)
    features = 'dns,tftp,dhcp,openscap'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'features': features},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain)
    assert set(files).issuperset(expected_files), assert_msg


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_all(sat_maintain, setup_backup_tests, module_synced_repos, backup_type):
    """Take a backup with all options provided

    :id: bbaf251f-7764-4b7d-b79b-f5f48f5d3b9e

    :parametrized: yes

    :steps:
        1. create an initial backup (for the sake of incremental)
        2. create another backup with all options provided

    :expectedresults:
        1. both backups succeed
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    instance = get_instance_name(sat_maintain)
    sat_maintain.execute(f'mkdir -m 0777 {subdir}')
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    init_backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]

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
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_negative_backup_nodir(sat_maintain, setup_backup_tests, module_synced_repos, backup_type):
    """Try to take a backup not providing a backup path

    :id: f55ff776-d08e-4317-b7a2-073cad91ce59

    :parametrized: yes

    :steps:
        1. try to create a backup without path provided

    :expectedresults:
        1. should fail with appropriate error message
    """
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir='',
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status != 0
    assert NODIR_MSG in str(result.stderr)


@pytest.mark.include_capsule
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_negative_backup_incremental_nodir(sat_maintain, setup_backup_tests, backup_type):
    """Try to take an incremental backup providing non-existing path to the previous backup
    (expected after --incremental option)

    :id: 4efec2fb-810b-4636-ae26-422a6bcb43cc

    :parametrized: yes

    :steps:
        1. try to create an incremental backup with non-existing path provided

    :expectedresults:
        1. should fail with appropriate error message
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir='',
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'incremental': subdir},
    )
    assert result.status != 0
    assert NOPREV_MSG in str(result.stderr)


@pytest.mark.include_capsule
def test_negative_restore_baddir_nodir(sat_maintain, setup_backup_tests):
    """Try to run restore with non-existing source dir provided

    :id: 65ccc0d0-ca43-4877-9b29-50037e378ca5

    :parametrized: yes

    :steps:
        1. try to run restore with non-existing path provided
        2. try to run restore without a backup dir

    :expectedresults:
        1. should fail with appropriate error message
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Restore.run(
        backup_dir=subdir,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status != 0
    assert BADDIR_MSG in str(result.stdout)
    result = sat_maintain.cli.Restore.run(
        backup_dir='',
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status != 0
    assert NODIR_MSG in str(result.stderr)


@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_puppet_backup_restore(
    sat_maintain,
    setup_backup_tests,
    module_synced_repos,
    backup_type,
):
    """Puppet backup/restore test.

    :id: 0f8555dc-8c1f-47cd-b5f6-5655d98564cd

    :parametrized: yes

    :steps:
        1. Enable puppet on the satellite
        2. create a backup of different types
        3. check that appropriate files are created
        4. restore the backup (installer --reset-data is run in this step)
        5. check system health
        6. check the content was restored

    :expectedresults:
        1. backup succeeds
        2. expected files are present in the backup
        3. restore succeeds
        4. system health check succeeds
        5. content is present after restore

    :customerscenario: true

    :BZ: 2158896
    """
    # Enable puppet on the Satellite
    sat_maintain.enable_puppet_satellite()

    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    instance = get_instance_name(sat_maintain)
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'skip-pulp-content': False},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain)
    assert set(files).issuperset(expected_files), assert_msg

    # Run restore
    sat_maintain.execute('rm -rf /var/lib/pulp/media/artifact')
    result = sat_maintain.cli.Restore.run(
        backup_dir=backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check the system health after restore
    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
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

    assert int(sat_maintain.run('find /var/lib/pulp/media/artifact -type f | wc -l').stdout) > 0


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.include_capsule
@pytest.mark.parametrize('skip_pulp', [False, True], ids=['include_pulp', 'skip_pulp'])
@pytest.mark.parametrize('backup_type', ['online', 'offline'])
def test_positive_backup_restore(
    sat_maintain,
    module_target_sat,
    module_capsule_configured,
    setup_backup_tests,
    module_synced_repos,
    backup_type,
    skip_pulp,
):
    """General backup/restore end-to-end test.

    :id: 4eec7790-b2d5-4aea-83ea-3f0db503e4b9

    :parametrized: yes

    :steps:
        1. create a backup of different types
        2. check that appropriate files are created
        3. restore the backup (installer --reset-data is run in this step)
        4. check system health
        5. check the content was restored

    :expectedresults:
        1. backup succeeds
        2. expected files are present in the backup
        3. restore succeeds
        4. system health check succeeds
        5. content is present after restore

    :customerscenario: true

    :Verifies: SAT-23093

    :BZ: 2172540, 1978764, 1979045
    """
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    instance = get_instance_name(sat_maintain)
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True, 'skip-pulp-content': skip_pulp},
        timeout='30m',
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check for expected files
    backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain, skip_pulp)
    assert set(files).issuperset(expected_files), assert_msg

    # Check if certificate tar file is present in Capsule backup.
    if instance == 'capsule':
        cert_file = sat_maintain.execute(
            f'tar -tvf {backup_dir}/config_files.tar.gz | grep {sat_maintain.hostname}'
        ).stdout
        assert f'{sat_maintain.hostname}-certs.tar' in cert_file

    # Run restore
    if not skip_pulp:
        sat_maintain.execute('rm -rf /var/lib/pulp/media/artifact')
    result = sat_maintain.cli.Restore.run(
        backup_dir=backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # Check the system health after restore
    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
    assert result.status == 0

    result = sat_maintain.cli.Service.status()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    # Check that content is present after restore
    if type(sat_maintain) is Satellite:
        repo = sat_maintain.api.Repository().search(
            query={'search': f'''name="{module_synced_repos['custom'].name}"'''}
        )[0]
        assert repo.id == module_synced_repos['custom'].id

        rh_repo = sat_maintain.api.Repository().search(
            query={'search': f'''name="{module_synced_repos['rh'].name}"'''}
        )[0]
        assert rh_repo.id == module_synced_repos['rh'].id
    else:
        repo_path = module_synced_repos['custom'].full_path.replace(
            module_target_sat.hostname, module_capsule_configured.hostname
        )
        repo_files = get_repo_files_by_url(repo_path)
        assert len(repo_files) == constants.FAKE_0_YUM_REPO_PACKAGES_COUNT

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
    instance = get_instance_name(sat_maintain)
    subdir = f'{BACKUP_DIR}backup-{gen_string("alpha")}'
    result = sat_maintain.cli.Backup.run_backup(
        backup_dir=subdir,
        backup_type=backup_type,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    init_backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]

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
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    # check for expected files
    inc_backup_dir = re.findall(rf'{subdir}\/{instance}-backup-.*-[0-5][0-9]', result.stdout)[0]
    files = sat_maintain.execute(f'ls -a {inc_backup_dir}').stdout.split('\n')
    files = [i for i in files if not re.compile(r'^\.*$').search(i)]

    expected_files = get_exp_files(sat_maintain)
    assert set(files).issuperset(expected_files), assert_msg

    # restore initial backup and check system health
    result = sat_maintain.cli.Restore.run(
        backup_dir=init_backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
    assert result.status == 0

    # check that the additional content is missing at this point
    result = sat_maintain.api.Repository().search(query={'search': f'name="{secondary_repo.name}"'})
    assert len(result) == 0

    # restore incremental backup and check system health
    result = sat_maintain.cli.Restore.run(
        backup_dir=inc_backup_dir,
        options={'assumeyes': True, 'plaintext': True},
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    result = sat_maintain.cli.Health.check(
        options={'whitelist': 'foreman-tasks-not-paused', 'assumeyes': True, 'plaintext': True}
    )
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
