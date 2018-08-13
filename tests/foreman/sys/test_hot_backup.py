# -*- encoding: utf-8 -*-
"""Test class for ``katello-backup``

:Requirement: HotBackup

:CaseAutomation: automated

:CaseLevel: System

:CaseComponent: Backup

:TestType: functional

:CaseImportance: High

:Upstream: No

:Setup: Populate a Satellite with hosts/repos/contents
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    BACKUP_FILES,
    FAKE_2_YUM_REPO,
    HOT_BACKUP_FILES,
)
from robottelo.decorators import (
    destructive,
    skip_if_bug_open,
    stubbed,
)
from robottelo.helpers import get_services_status
from robottelo.ssh import get_connection
from robottelo.test import TestCase
from time import sleep

BCK_MSG = 'BACKUP Complete, contents can be found in: /tmp/{0}'
BADPREV_MSG = 'Previous backup directory does not exist: {0}'
NODIR_MSG = 'ERROR: Please specify an export directory'
NOARG_MSG = 'missing argument'


def make_random_tmp_directory(connection):
    name = gen_string('alpha')
    connection.run('rm -rf /tmp/{0}'.format(name))
    connection.run('mkdir -p /tmp/{0}'.format(name))
    return name


def tmp_directory_cleanup(connection, *args):
    for name in args:
        connection.run('rm -rf /tmp/{0}'.format(name))


def directory_size_compare(connection, full_dir, inc_dir):
    size_full = connection.run(
            "du -s /tmp/{0}/satellite-backup* | cut -f1".format(full_dir))
    size_inc = connection.run(
            "du -s /tmp/{0}/satellite-backup* | cut -f1".format(inc_dir))
    if size_full.stdout[0] > size_inc.stdout[0]:
        return True
    else:
        return False


@destructive
class HotBackupTestCase(TestCase):
    """Implements ``katello-backup`` tests"""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(HotBackupTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()
        repo = entities.Repository(
            url=FAKE_2_YUM_REPO,
            content_type='yum',
            download_policy='immediate',
            product=cls.product,
        ).create()
        repo.sync()

    def tearDown(self):
        """Make sure services are started after each test"""
        with get_connection() as connection:
            result = connection.run(
                'katello-service start',
                timeout=1600,
                output_format='plain'
            )
            if result.return_code != 0:
                self.fail('Failed to start services')
        super(HotBackupTestCase, self).tearDown()

    def check_services_status(self, max_attempts=5):
        for _ in range(max_attempts):
            try:
                result = get_services_status()
                self.assertEquals(result[0], 0)
            except AssertionError:
                sleep(30)
            else:
                break
        else:
            raise AssertionError(
                u'Some services failed to start:\
                \n{0}'.format('\n'.join(result[1])))

    @destructive
    def test_positive_online_backup_with_existing_directory(self):
        """katello-backup --online-backup with existing directory

        :id: 3f8285d5-c68b-4d84-8568-bcd7e4f7f19e

        :Steps:

            1. Create a directory (ie /tmp/xyz)
            2. Run ``katello-backup --online-backup /tmp/xyz``

        :expectedresults: The backup is successfully created in existing folder
            and contains all the default files needed to restore. Services keep
            running.

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            connection.run('katello-service start')
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/satellite-backup*'.format(dir_name),
            )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            # check if services are running correctly
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_positive_online_backup_with_directory_created(self):
        """katello-backup --online with non-existing directory


        :id: 946991ad-125a-4f24-a33e-ea27fce38eda

        :Steps:

            1. Ensure the directory /tmp/xyz does not exist.
            2. Run ``katello-backup --online-backup /tmp/xyz``

        :expectedresults: ``/tmp/xyz`` is created and the backup is saved to it
            containing all the default files needed to restore. Services
            keep running.

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = gen_string('alpha')
            tmp_directory_cleanup(connection, dir_name)
            connection.run('katello-service start')
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/satellite-backup*'.format(dir_name),
            )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            # check if services are running correctly
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_negative_online_backup_with_no_directory(self):
        """katello-backup --online-backup with no directory

        :id: e5f58d05-1043-48c0-971f-8f30cc8642ed

        :Steps:

            1. Run ``katello-backup --online-backup``

        :expectedresults: The error message is shown, services are not
            stopped

        :caseautomation: automated
        """
        with get_connection() as connection:
            connection.run('katello-service start')
            result = connection.run(
                'satellite-backup -y --online-backup',
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(NODIR_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_backup_with_no_directory(self):
        """katello-backup with no directory specified

        :id: 5b1efcc6-990c-43af-b6c5-1b9b40002cb0

        :Steps:

            1. Run ``katello-backup``

        :expectedresults: The error message is shown, services are not
            stopped

        :caseautomation: automated
        """
        with get_connection() as connection:
            connection.run('katello-service start')
            result = connection.run(
                'satellite-backup -y',
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(NODIR_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_positive_online_backup_exit_code_on_failure(self):
        """katello-backup --online-backup correct exit code on failure

        :id: a26795bf-faa4-49ce-8613-2ed7bc9c0540

        :Steps:

            1. Stop the postgresql service
            2. Run ``katello-backup --online-backup``
            3. Assert exit code is not 0
            4. Start the service again

        :bz: 1323607

        :expectedresults: katello-backup finished with correct exit code

        :caseautomation: automated
        """
        with get_connection() as connection:
            connection.run('katello-service start')
            dir_name = gen_string('alpha')
            dead_service = 'postgresql'
            connection.run('service {0} stop'.format(dead_service))
            tmp_directory_cleanup(connection, dir_name)
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(dir_name)
            )
            self.assertNotEqual(result.return_code, 0)
            connection.run('service {0} start'.format(dead_service))
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_positive_online_skip_pulp(self):
        """Katello-backup --online-backup with --skip-pulp-content
        option should not create pulp files in destination.

        :id: 0f0c1915-dd07-4571-9b05-e0778efc85b2

        :Steps:

            1. Run online backup with --skip-pulp-content option
            2. List contents of the destination

        :expectedresults: ``/tmp/bck-no-pulp`` is created and pulp
            related files are not present. Services keep running.

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            connection.run('katello-service start')
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup '
                '--skip-pulp-content'.format(dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(dir_name),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_positive_skip_pulp(self):
        """Katello-backup with --skip-pulp-content option should not
        create pulp files in destination.

        :id: f0fa2daa-209e-4d46-9b67-3041768a2a77

        :Steps:

            1. Run online backup with --skip-pulp-content option
            2. List contents of the destination

        :expectedresults: Backup is created and pulp related
            files are not present. Services are started back again.

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'satellite-backup -y /tmp/{0} '
                '--skip-pulp-content'.format(dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(dir_name),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_positive_logical_db_backup(self):
        """Katello-backup with --logical-db-backup option should
        dump full database schema during offline backup

        :id: a1386cfa-cd7e-4f22-9ebc-7c908d514ad4

        :Steps:

            1. Run online backup with --logical-db-backup option
            2. List contents of the destination

        :expectedresults: Backup is created and additional files are
            not present. Services are started back again.

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'satellite-backup -y /tmp/{0} '
                '--logical-db-backup'.format(dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(dir_name),
                    'list'
                    )
            self.assertTrue(set(files.stdout).issuperset(
                set(BACKUP_FILES)))
            self.assertIn(u'candlepin.dump', files.stdout)
            self.assertIn(u'foreman.dump', files.stdout)
            self.assertIn(u'mongo_dump', files.stdout)
            self.assertIn(u'pg_globals.dump', files.stdout)
            # check if services are running correctly
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    def test_positive_incremental(self):
        """Katello-backup with --incremental option

        :id: 3bd1e85c-8c95-4198-a126-35eaf14572ed

        :Steps:

            1. Run full backup
            2. Run incremental backup from the previous backup

        :expectedresults: Incremental backup is created. Services are
            started back again.

        :caseautomation: automated
        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result_full = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result_full.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result_full.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dir),
                    'list'
                    )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))

            # run incremental backup
            b1_dest = make_random_tmp_directory(connection)
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(b1_dir),
                    'list'
                    )
            result_inc = connection.run(
                'satellite-backup -y /tmp/{0} --incremental /tmp/{1}/{2}'
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result_inc.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result_inc.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertTrue(set(files.stdout).issuperset(set(BACKUP_FILES)))
            # check if services are running correctly
            self.check_services_status()
            self.assertTrue(
                    directory_size_compare(connection, b1_dir, b1_dest))
            tmp_directory_cleanup(connection, b1_dir, b1_dest)

    @destructive
    def test_negative_incremental_with_no_src_directory(self):
        """katello-backup --incremental with no source directory

        :id: 8bb36ffe-822e-448e-88cd-93885efd59a7

        :Steps:

            1. Run ``katello-backup --incremental``

        :bz: 1447619

        :expectedresults: The error message is shown, services are not
            stopped

        :caseautomation: automated
        """
        with get_connection() as connection:
            result = connection.run(
                'satellite-backup --incremental',
                output_format='plain'
            )
            self.assertNotEqual(result.return_code, 0)
            self.assertIn(NOARG_MSG, result.stdout)
            self.check_services_status()

    @destructive
    def test_negative_incremental_with_no_dest_directory(self):
        """katello-backup --incremental with no destination directory

        :id: 183195df-b5df-4edf-814e-221bbcdcbde1

        :Steps:

            1. Run ``katello-backup --incremental /tmp``

        :expectedresults: The error message is shown, services are not
            stopped

        :caseautomation: automated
        """
        with get_connection() as connection:
            result = connection.run(
                'satellite-backup -y --incremental /tmp',
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(NODIR_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_incremental_with_invalid_dest_directory(self):
        """katello-backup --incremental with invalid destination directory

        :id: 1667f35e-049e-4a1a-ae7a-a2da6661b3d8

        :Steps:

            1. Run ``katello-backup /tmp --incremental nonexistent``

        :expectedresults: The error message is shown, services are not
            stopped

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = gen_string('alpha')
            tmp_directory_cleanup(connection, dir_name)
            result = connection.run(
                'satellite-backup -y /tmp --incremental {0}'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(BADPREV_MSG.format(dir_name), result.stderr)
            self.check_services_status()

    @destructive
    def test_positive_online_incremental_skip_pulp(self):
        """Katello-backup with --online --skip-pulp-content and
        --incremental options

        :id: 49c42a81-88c3-4827-9b9e-6c41a8570234

        :Steps:

            1. Run full backup
            2. Run online incremental backup without pulp from the
                previous backup

        :expectedresults: Incremental backup is created and pulp related files
            are not present. Services keep running.

        :caseautomation: automated
        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            connection.run('katello-service start')
            # run full backup
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dir),
                    'list'
                    )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))

            # run incremental backup
            b1_dest = make_random_tmp_directory(connection)
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(b1_dir),
                    'list'
                    )
            result = connection.run(
                '''katello-backup -y --online-backup \
                        --skip-pulp-content /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            # check if services are running correctly
            self.check_services_status()
            self.assertTrue(
                    directory_size_compare(connection, b1_dir, b1_dest))
            tmp_directory_cleanup(connection, b1_dir, b1_dest)

    @destructive
    def test_positive_incremental_skip_pulp(self):
        """Katello-backup with --skip-pulp-content and --incremental
        options

        :id: b2e6095c-648c-48a2-af5b-212c9d7e18e6

        :Steps:

            1. Run full backup
            2. Run incremental backup without pulp from the previous backup

        :expectedresults: Incremental backup is created with and pulp related
            files are not present. Services are started back again.

        :caseautomation: automated
        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dir),
                    'list'
                    )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))

            # run incremental backup
            b1_dest = make_random_tmp_directory(connection)
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(b1_dir),
                    'list'
                    )
            result = connection.run(
                '''satellite-backup  -y \
                        --skip-pulp-content /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            # check if services are running correctly
            self.check_services_status()
            self.assertTrue(
                    directory_size_compare(connection, b1_dir, b1_dest))
            tmp_directory_cleanup(connection, b1_dir, b1_dest)

    @destructive
    @skip_if_bug_open('bugzilla', 1527957)
    def test_positive_online_incremental(self):
        """Make an incremental online backup

        :id: a5b3536f-8365-41c7-9386-cddde588fe8c

        :Steps:

            1. Run full backup (base)
            2. Make config change c1
            3. Run incremental backup ib1
            4. Restore base backup, verify c1 config doesnt not exist
            5. restore ib1, verify c1 config does exist

        :bz: 1445871, 1482135

        :expectedresults: Backup "ib1" is backed up.

        :caseautomation: automated
        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            connection.run('katello-service start')
            # run full backup
            result = connection.run(
                'satellite-backup -y /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/satellite-backup*'.format(b1_dir),
                    'list'
                    )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))

            # Create a new repo
            repo_name = gen_string('alpha')
            entities.Repository(
                    product=self.product, name=repo_name
            ).create()

            # run incremental backup /tmp/ib1
            ib1_dir = gen_string('alpha')
            # destination directory for incremental backup
            ib1_dest = gen_string('alpha')
            connection.run('cp -r /tmp/{0} /tmp/{1}'.format(b1_dir, ib1_dir))
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(ib1_dir),
                    'list'
            )
            result = connection.run(
                '''satellite-backup -y \
                        --online-backup /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(ib1_dest, ib1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(ib1_dest), result.stdout)

            # restore /tmp/b1 and assert repo 1 is not there
            result = connection.run(
                    'satellite-restore -y /tmp/{0}/satellite-backup*'
                    .format(b1_dir),
                    timeout=1600)
            self.assertEqual(result.return_code, 0)
            repo_list = entities.Repository().search(
                query={'search': 'name={0}'.format(repo_name)}
            )
            self.assertEqual(len(repo_list), 0)

            # restore /tmp/ib1 and assert repo 1 is there
            result = connection.run(
                    'satellite-restore -y /tmp/{0}/satellite-backup*'
                    .format(ib1_dest),
                    timeout=1600)
            self.assertEqual(result.return_code, 0)
            repo_list = entities.Repository().search(
                query={'search': 'name={0}'.format(repo_name)}
            )
            self.assertEqual(len(repo_list), 1)
            self.assertTrue(
                    directory_size_compare(connection, b1_dir, ib1_dest))
            tmp_directory_cleanup(connection, b1_dir, ib1_dir, ib1_dest)

    @destructive
    @stubbed()
    def test_positive_pull_content(self):
        """Pull content while a backup is running.

        :id: 1026f5f5-4180-4215-acce-876dd2d09ba9

        :Steps:

            1. Start a backup
            2. While backing up, have a host pull content from the satellite.

        :expectedresults: The backup succeeds  and the host gets the requested
            content.

        :caseautomation: notautomated
        """

@destructive
class ForemanMaintainBackupTestCase(TestCase):
    """Implements `foreman-maintain backup`` tests"""

    @classmethod
    def setUpClass(cls):
        """check if foreman maintain is installed"""
        # TODO

    def check_services_status(self, max_attempts=5):
        for _ in range(max_attempts):
            try:
                result = get_services_status()
                self.assertEquals(result[0], 0)
            except AssertionError:
                sleep(30)
            else:
                break
        else:
            raise AssertionError(
                u'Some services failed to start:\
                \n{0}'.format('\n'.join(result[1])))

    def test_positive_online(self):
        """foreman-manintain online backup

        :id: afea1280-0d90-4f4d-ad88-f259a4f37fc7

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = gen_string('alpha')
            result = connection.run(
                'foreman-maintain backup online -y /tmp/{0}'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/foreman-backup*'.format(dir_name),
            )
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    def test_positive_online_skip_pulp_preserve_dir(self):
        """online backup with --skip_pulp and --preserve-directory

        :id: 3b7325e9-defb-4ca5-9a55-0f7543304d08

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            # postgre access needed for --preserve-dir
            connection.run('chown :postgres /tmp/{0}'.format(dir_name))
            result = connection.run(
                'foreman-maintain backup online -y \
                        --skip-pulp-content \
                        --preserve-directory /tmp/{0}'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/'.format(dir_name),
            )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    def test_positive_online_incremental(self):

        """online backup with --split-pulp-tar and --incremental

        :id: 47da5fdb-d429-404a-883a-7ac12002f4b6

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'foreman-maintain backup online -y \
                        --split-pulp-tar 10M \
                        /tmp/{0}'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/foreman-backup*'.format(b1_dir),
                    'list'
                    )
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            # TODO check if none of pulp data is bigger than 10240

            # run incremental backup
            b1_dest = make_random_tmp_directory(connection)
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(b1_dir),
                    'list'
                    )
            result = connection.run(
                '''foreman-maintain backup online -y \
                        --skip-pulp-content \
                        --incremental /tmp/{1}/{2} \
                        /tmp/{0}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/foreman-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.check_services_status()
            tmp_directory_cleanup(connection, b1_dir, b1_dest)
            # TODO better check incremental -- e.g. what is in tar

    def test_positive_offline(self):
        """offline backup, offline

        :id: 8d3faae6-6d25-4c90-abfa-6ed993c1e527

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = gen_string('alpha')
            result = connection.run(
                'foreman-maintain backup offline -y /tmp/{0}'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/foreman-backup*'.format(dir_name),
            )
            self.assertTrue(set(files.stdout).issuperset(
                set(BACKUP_FILES)))
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    def test_positive_offline_skip_pulp_and_preserve_dir(self):

        """offline backup with --skip-pulp-content and --preserve-dir
        --include-online

        :id: a57b37ee-9f90-4c4e-8744-d5e1f0ea6d86

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            # postgre access needed for --preserve-dir
            connection.run('chown :postgres /tmp/{0}'.format(dir_name))
            result = connection.run(
                'foreman-maintain backup offline -y \
                        --skip-pulp-content \
                        --preserve-directory /tmp/{0}'.format(
                    dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/'.format(dir_name),
            )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.check_services_status()
            tmp_directory_cleanup(connection, dir_name)

    def test_positive_offline_incremental(self):

        """offline backup with --split-pulp-tar and --incremental

        :id: 1cad5b2a-a480-4db1-b4bc-726d342210fe

        :Steps:

            1.
            2.

        :expectedresults:

        :caseautomation: automated
        """

        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'foreman-maintain backup offline -y \
                        --split-pulp-tar 10M \
                        /tmp/{0}'.format(b1_dir),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/foreman-backup*'.format(b1_dir),
                    'list'
                    )
            self.assertTrue(set(files.stdout).issuperset(
                set(BACKUP_FILES)))
            # TODO check if none of pulp data is bigger than 10240

            # run incremental backup
            b1_dest = make_random_tmp_directory(connection)
            timestamped_dir = connection.run(
                    'ls /tmp/{0}/'.format(b1_dir),
                    'list'
                    )
            result = connection.run(
                '''foreman-maintain backup offline -y \
                        --skip-pulp-content \
                        --incremental /tmp/{1}/{2} \
                        /tmp/{0}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/foreman-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.check_services_status()
            tmp_directory_cleanup(connection, b1_dir, b1_dest)
            # TODO better check incremental -- e.g. what is in tar
