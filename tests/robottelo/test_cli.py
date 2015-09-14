import unittest2

from robottelo.cli.base import Base
from robottelo.config import conf
from robottelo.ssh import SSHCommandResult


class CLIClass(Base):
    """Class used for the username and password lookup tests"""
    foreman_admin_username = 'adminusername'
    foreman_admin_password = 'adminpassword'


class BaseCliTestCase(unittest2.TestCase):
    """Tests for the Base cli class"""
    def setUp(self):  # noqa
        super(BaseCliTestCase, self).setUp()
        self.old_properties = conf.properties.copy()
        conf.properties['foreman.admin.username'] = 'configusername'
        conf.properties['foreman.admin.password'] = 'configpassword'

    def tearDown(self):  # noqa
        super(BaseCliTestCase, self).tearDown()
        conf.properties = self.old_properties

    def test_construct_command(self):
        """_construct_command builds a command using flags and arguments"""
        Base.command_base = 'basecommand'
        Base.command_sub = 'subcommand'
        command_parts = Base._construct_command({
            u'flag-one': True,
            u'flag-two': False,
            u'argument': u'value',
            u'ommited-arg': None,
        }).split()

        self.assertIn(u'basecommand', command_parts)
        self.assertIn(u'subcommand', command_parts)
        self.assertIn(u'--flag-one', command_parts)
        self.assertIn(u'--argument="value"', command_parts)
        self.assertNotIn(u'--flag-two', command_parts)
        self.assertEqual(len(command_parts), 4)

    def test_username_password_parameters_lookup(self):
        """Username and password returned are the parameters"""
        username, password = CLIClass._get_username_password('auser', 'apass')

        self.assertEqual(username, 'auser')
        self.assertEqual(password, 'apass')

    def test_username_password_attributes_lookup(self):
        """Username and password returned are the class attributes"""
        username, password = CLIClass._get_username_password()

        self.assertEqual(username, CLIClass.foreman_admin_username)
        self.assertEqual(password, CLIClass.foreman_admin_password)

    def test_username_password_config_lookup(self):
        """Username and password returned are from configuration"""
        username, password = Base._get_username_password()

        self.assertEqual(username, conf.properties['foreman.admin.username'])
        self.assertEqual(password, conf.properties['foreman.admin.password'])

    def test_with_user(self):
        """Check if ``with_user`` method returns a right wrapper class"""
        new_class = Base.with_user('auser', 'apass')

        self.assertEqual(new_class.foreman_admin_username, 'auser')
        self.assertEqual(new_class.foreman_admin_password, 'apass')
        self.assertIn(Base, new_class.__bases__)

    def test_remove_task_status(self):
        """Check if ``_remove_task_status`` method cleans the expected task
        status messages.

        """
        data = (
            u'Task 3af6fec3-2b7d-4e8a-93a4-082509e203fc running: 0.005/1, 0%, '
            '0.0/s, elapsed: 00:00:02, ETA: 00:07:34\nTask '
            '3af6fec3-2b7d-4e8a-93a4-082509e203fc success: 1.0/1, 100%, '
            '0.1/s, elapsed: 00:00:11\nTask '
            '3af6fec3-2b7d-4e8a-93a4-082509e203fc success: 1.0/1, 100%, '
            '0.1/s, elapsed: 00:00:11\nTask '
            '6ba9d82a-ea55-4934-8aab-0e057102ee11 running: 0.005/1, 0%, '
            '0.0/s, elapsed: 00:00:02, ETA: 00:06:55\nTask '
            '6ba9d82a-ea55-4934-8aab-0e057102ee11 running: 0.005/1, 0%, '
            '0.0/s, elapsed: 00:00:02, ETA: 00:06:55\n\n'
        )
        result = SSHCommandResult(stderr=data, return_code=0)
        self.assertEqual(Base._remove_task_status(result).stderr, '')
