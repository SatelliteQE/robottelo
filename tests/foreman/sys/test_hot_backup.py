# -*- encoding: utf-8 -*-
"""Test class for ``katello-backup``

:Requirement: HotBackup

:CaseAutomation: notautomated

:CaseLevel: System

:CaseComponent: Backup

:TestType: functional

:CaseImportance: High

:Upstream: No

:Setup: Populate a Satellite with hosts/repos/contents
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo import ssh
from robottelo.constants import BACKUP_FILES, HOT_BACKUP_FILES
from robottelo.decorators import (
        bz_bug_is_open,
        destructive,
        skip_if_bug_open,
        stubbed,
)
from robottelo.helpers import get_services_status
from robottelo.ssh import get_connection
from robottelo.test import TestCase

BCK_MSG = 'BACKUP Complete, contents can be found in: /tmp/{0}'


def make_random_tmp_directory(connection):
    name = gen_string('alpha')
    connection.run('rm -rf /tmp/{0}'.format(name))
    connection.run('mkdir -p /tmp/{0}'.format(name))
    return name


def tmp_directory_cleanup(connection, *args):
    for name in args:
        connection.run('rm -rf /tmp/{0}'.format(name))


@destructive
class HotBackupTestCase(TestCase):
    """Implements ``katello-backup`` tests"""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(HotBackupTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

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

        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/katello-backup*'.format(dir_name),
            )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            # check if services are running correctly
            self.assertTrue(get_services_status())
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

        """
        with get_connection() as connection:
            dir_name = gen_string('alpha')
            connection.run('rm -rf /tmp/{0}'.format(dir_name))
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                'ls -a /tmp/{0}/katello-backup*'.format(dir_name),
            )
            # backup could have more files than the default so it is superset
            self.assertTrue(set(files.stdout).issuperset(
                set(HOT_BACKUP_FILES)))
            # check if services are running correctly
            self.assertTrue(get_services_status())
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

        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup '
                '--skip-pulp-content'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(dir_name),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.assertTrue(get_services_status())
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

        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'katello-backup /tmp/{0} '
                '--skip-pulp-content'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(dir_name), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(dir_name),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.assertTrue(get_services_status())
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

        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dir),
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
                'katello-backup /tmp/{0} --incremental /tmp/{1}/{2}'
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertTrue(set(files.stdout).issuperset(set(BACKUP_FILES)))
            # check if services are running correctly
            self.assertTrue(get_services_status())
            tmp_directory_cleanup(connection, b1_dir, b1_dest)

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

        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dir),
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
                '''katello-backup --online-backup \
                        --skip-pulp-content /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            rhel_release = ssh.command('lsb_release -r --short | cut -c1-1')
            if not bz_bug_is_open(1445224) or rhel_release == 6:
                self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.assertTrue(get_services_status())
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

        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dir),
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
                '''katello-backup \
                        --skip-pulp-content /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(b1_dest, b1_dir, timestamped_dir.stdout[0]),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dest), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dest),
                    'list'
                    )
            self.assertNotIn(u'pulp_data.tar', files.stdout)
            rhel_release = ssh.command('lsb_release -r --short | cut -c1-1')
            if not bz_bug_is_open(1445224) or rhel_release == 6:
                self.assertNotIn(u'.pulp.snar', files.stdout)
            # check if services are running correctly
            self.assertTrue(get_services_status())
            tmp_directory_cleanup(connection, b1_dir, b1_dest)

    @destructive
    @skip_if_bug_open('bugzilla', 1435333)
    def test_positive_online_incremental(self):
        """Make an incremental online backup

        :id: a5b3536f-8365-41c7-9386-cddde588fe8c

        :Steps:

            1. Run full backup (base)
            2. Make config change c1
            3. Run incremental backup ib1
            4. Restore base backup, verify c1 config doesnt not exist
            5. restore ib1, verify c1 config does exist

        :expectedresults: Backup "ib1" is backed up.

        """
        with get_connection() as connection:
            b1_dir = make_random_tmp_directory(connection)
            # run full backup
            result = connection.run(
                'katello-backup /tmp/{0} --online-backup'.format(b1_dir),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(b1_dir), result.stdout)
            files = connection.run(
                    'ls -a /tmp/{0}/katello-backup*'.format(b1_dir),
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
                '''katello-backup \
                        --online-backup /tmp/{0} \
                        --incremental /tmp/{1}/{2}'''
                .format(ib1_dest, ib1_dir, timestamped_dir.stdout[0]),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG.format(ib1_dest), result.stdout)

            # restore /tmp/b1 and assert repo 1 is not there
            connection.run(
                    'katello-restore -y /tmp/{0}/katello-backup*'
                    .format(b1_dir))
            repo_list = entities.Repository().search(
                query={'search': 'name={0}'.format(repo_name)}
            )
            self.assertEqual(len(repo_list), 0)

            # restore /tmp/ib1 and assert repo 1 is there
            connection.run(
                    'katello-restore -y /tmp/{0}/katello-backup*'
                    .format(ib1_dest))
            repo_list = entities.Repository().search(
                query={'search': 'name={0}'.format(repo_name)}
            )
            self.assertEqual(len(repo_list), 1)
            tmp_directory_cleanup(connection, b1_dir, ib1_dir, ib1_dest)

    @destructive
    @stubbed()
    def test_positive_restore_after_update(self):
        """Restore from a backup in updated version of satellite

        :id: 2069b860-43d4-4b65-a8cd-89a8b2feafbe

        :Steps:

            1. Create backup from previous version of satellite
            2. Update satellite to latest version
            3. Restore online backup
            4. Restore offline backup
            5. Restore online incremental backup
            6. Restore offline incremental backup

        :expectedresults: Each backup is fully restored.

        :CaseAutomation: notautomated

        """
        # IS THIS CASE REASONABLE?

    @destructive
    @stubbed()
    def test_positive_restore(self):
        """Restore to a Satellite with config that has been updated since the
        backup

        :id: 03a47dec-9cd4-4cae-88ec-c19dfaa1d5ad

        :Steps:

            1. Restore online backup
            2. Restore offline backup
            3. Restore online incremental backup
            4. Restore offline incremental backup

        :expectedresults: Each backup is fully restored.

        :CaseAutomation: notautomated

        """

    @destructive
    @stubbed()
    def test_positive_load_backup(self):
        """Load testing, backup

        :id: b0d7de3a-d1d5-4cb9-8041-47301b658408

        :Steps:
            1. Create load on the Satellite by having multiple host pull
               content.
            2. Run a backup while the Satellite is under load
            3. Restore the backup

        :expectedresults: The backup is successful and the restored
            configuration is correct.

        :CaseAutomation: notautomated

        """

    @destructive
    @stubbed()
    def test_positive_load_restore(self):
        """Load testing, restore

        :id: c0347aee-48b4-45da-92ef-1e92397c5543

        :Steps:

            1. Run a backup.
            2. Run a restore.

        :expectedresults: The restore is successful.

        :CaseAutomation: notautomated

        """

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

        :CaseAutomation: notautomated

        """
