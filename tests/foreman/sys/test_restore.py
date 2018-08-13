# -*- encoding: utf-8 -*-
"""Test class for ``katello-restore``

:Requirement: katello-restore

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Backup

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import destructive, skip_if_bug_open
from robottelo.helpers import get_services_status
from robottelo.ssh import get_connection
from robottelo.test import TestCase
from time import sleep

NOVALID_MSG = 'Please specify the backup directory to restore'
NOEXIST_MSG = 'Backup directory does not exist'
NOFILES_MSG = 'Cannot find the required'


def make_random_tmp_directory(connection):
    name = gen_string('alpha')
    connection.run('rm -rf /tmp/{0}'.format(name))
    connection.run('mkdir -p /tmp/{0}'.format(name))
    return name


def tmp_directory_cleanup(connection, *args):
    for name in args:
        connection.run('rm -rf /tmp/{0}'.format(name))

@destructive
class ForemanMaintainRestoreTestCase(TestCase):
    """Implements ``foreman-maintain restore`` tests"""

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
        super(ForemanMaintainRestoreTestCase, self).tearDown()

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
    def test_negative_restore_no_directory(self):
        """run foreman-maintain restore with no directory specified

        :id: 61952f9b-1dbe-4154-83b6-f452eed798d6

        :Steps:

            1. Run ``foreman-maintain restore``

        :bz: 1451833

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            result = connection.run(
                'foreman-maintain restore',
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            #self.assertIn(NOVALID_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_restore_nonexistent_directory(self):
        """run foreman-maintain restore with nonexistent directory specified

        :id: d825c43e-1be0-4aea-adcf-23fcf98e73c8

        :Steps:

            1. Run ``foreman-maintain restore`` fake_dir_name

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            name = gen_string('alpha')
            result = connection.run(
                'foreman-maintain restore {}'.format(name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            #self.assertIn(NOEXIST_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_restore_with_empty_directory(self):
        """katello-backup with no directory specified

        :id: e229a4e0-4944-4369-ab7f-0f4e65480e47

        :Steps:

            1. Run ``katello-backup`` empty_dir

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'foreman-maintain restore -y /tmp/{}'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            #self.assertIn(NOFILES_MSG, result.stdout)
            self.check_services_status()

    @destructive
    def test_positive_restore_from_offline_backup(self):
        """foreman-maintain restore from offline backup files

        :id: d270bf40-7999-4b80-a38e-1d861a966cd9

        :Steps:

            1. Add a new user
            2. Create an offline backup
            3. Add another user
            4. Restore from backup

        :bz: 1482135

        :expectedresults: Restore is successful. User 1 is
            present after restoring, User 2 is not

        """
        with get_connection() as connection:
            username1 = gen_string('alpha')
            username2 = gen_string('alpha')
            dir_name = make_random_tmp_directory(connection)
            entities.User(login=username1).create()
            result = connection.run(
                'foreman-maintain backup offline -y '
                '--skip-pulp-content  /tmp/{0}'.format(dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            entities.User(login=username2).create()
            result = connection.run(
                'foreman-maintain restore -y /tmp/{0}/katello-backup*'
                .format(dir_name),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertNotIn(username2, username_list)
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    @skip_if_bug_open('bugzilla', 1527957)
    def test_positive_restore_from_online_and_incremental(self):
        """foreman-maintain restore from online and incremental backup

        :id: 8e564f44-06f4-47f0-8c0b-4e3a62af7915

        :Steps:

            1. Create a User
            2. Create an online backup
            3. Create another User
            4. Create an incremental backup
            5. Restore from online backup
            6. Restore from incremental backup

        :bz: 1482135

        :expectedresults: Both restores are successful. User 1
            is present after restoring from online backup, User 2
            is not. Both Users are present after restoring from
            incremental.

        """
        with get_connection() as connection:
            b1 = make_random_tmp_directory(connection)
            b2 = make_random_tmp_directory(connection)
            username1 = gen_string('alpha')
            username2 = gen_string('alpha')
            entities.User(login=username1).create()
            result = connection.run(
                'foreman-maintain backup online -y'
                '--skip-pulp-content /tmp/{0}'.format(b1),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            entities.User(login=username2).create()
            result = connection.run(
                'foreman-maintain backup online -y '
                '--skip-pulp-content '
                '--incremental /tmp/{1}/* /tmp/{0}'
                .format(b2, b1),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)

            # restore from the base backup
            result = connection.run(
                'foreman-maintain restore -y /tmp/{0}/katello-backup*'
                .format(b1),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertNotIn(username2, username_list)

            # restore from the incremental backup
            result = connection.run(
                'foreman-maintain restore -y /tmp/{0}/katello-backup*'
                .format(b2),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertIn(username2, username_list)
            tmp_directory_cleanup(connection, b1, b2)


@destructive
class RestoreTestCase(TestCase):
    """Implements ``katello-restore`` tests"""

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
        super(RestoreTestCase, self).tearDown()

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
    def test_negative_restore_no_directory(self):
        """run katello-restore with no directory specified

        :id: 61952f9b-1dbe-4154-83b6-f452eed798d6

        :Steps:

            1. Run ``katello-restore``

        :bz: 1451833

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            result = connection.run(
                'satellite-restore',
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(NOVALID_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_restore_nonexistent_directory(self):
        """run katello-restore with nonexistent directory specified

        :id: d825c43e-1be0-4aea-adcf-23fcf98e73c8

        :Steps:

            1. Run ``katello-restore`` fake_dir_name

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            name = gen_string('alpha')
            result = connection.run(
                'satellite-restore {}'.format(name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 1)
            self.assertIn(NOEXIST_MSG, result.stderr)
            self.check_services_status()

    @destructive
    def test_negative_restore_with_empty_directory(self):
        """katello-backup with no directory specified

        :id: e229a4e0-4944-4369-ab7f-0f4e65480e47

        :Steps:

            1. Run ``katello-backup`` empty_dir

        :expectedresults: The error message is shown, services are not
            stopped

        """
        with get_connection() as connection:
            dir_name = make_random_tmp_directory(connection)
            result = connection.run(
                'satellite-restore -y /tmp/{}'.format(dir_name),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 255)
            self.assertIn(NOFILES_MSG, result.stdout)
            self.check_services_status()

    @destructive
    def test_positive_restore_from_offline_backup(self):
        """katello-restore from offline backup files

        :id: d270bf40-7999-4b80-a38e-1d861a966cd9

        :Steps:

            1. Add a new user
            2. Create an offline backup
            3. Add another user
            4. Restore from backup

        :bz: 1482135

        :expectedresults: Restore is successful. User 1 is
            present after restoring, User 2 is not

        """
        with get_connection() as connection:
            username1 = gen_string('alpha')
            username2 = gen_string('alpha')
            dir_name = make_random_tmp_directory(connection)
            entities.User(login=username1).create()
            result = connection.run(
                'satellite-backup -y /tmp/{0} '
                '--skip-pulp-content'.format(dir_name),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            entities.User(login=username2).create()
            result = connection.run(
                'satellite-restore -y /tmp/{0}/satellite-backup*'
                .format(dir_name),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertNotIn(username2, username_list)
            tmp_directory_cleanup(connection, dir_name)

    @destructive
    @skip_if_bug_open('bugzilla', 1527957)
    def test_positive_restore_from_online_and_incremental(self):
        """katello-restore from online and incremental backup

        :id: 8e564f44-06f4-47f0-8c0b-4e3a62af7915

        :Steps:

            1. Create a User
            2. Create an online backup
            3. Create another User
            4. Create an incremental backup
            5. Restore from online backup
            6. Restore from incremental backup

        :bz: 1482135

        :expectedresults: Both restores are successful. User 1
            is present after restoring from online backup, User 2
            is not. Both Users are present after restoring from
            incremental.

        """
        with get_connection() as connection:
            b1 = make_random_tmp_directory(connection)
            b2 = make_random_tmp_directory(connection)
            username1 = gen_string('alpha')
            username2 = gen_string('alpha')
            entities.User(login=username1).create()
            result = connection.run(
                'satellite-backup -y /tmp/{0} '
                '--online-backup '
                '--skip-pulp-content'.format(b1),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)
            entities.User(login=username2).create()
            result = connection.run(
                'satellite-backup -y '
                '--skip-pulp-content '
                '--online-backup /tmp/{0} '
                '--incremental /tmp/{1}/*'
                .format(b2, b1),
                output_format='plain',
                timeout=900
            )
            self.assertEqual(result.return_code, 0)

            # restore from the base backup
            result = connection.run(
                'satellite-restore -y /tmp/{0}/satellite-backup*'
                .format(b1),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertNotIn(username2, username_list)

            # restore from the incremental backup
            result = connection.run(
                'satellite-restore -y /tmp/{0}/satellite-backup*'
                .format(b2),
                timeout=1600)
            self.assertEqual(result.return_code, 0)
            user_list = entities.User().search()
            self.assertGreater(len(user_list), 0)
            username_list = [user.login for user in user_list]
            self.assertIn(username1, username_list)
            self.assertIn(username2, username_list)
            tmp_directory_cleanup(connection, b1, b2)
