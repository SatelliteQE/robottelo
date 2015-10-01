import mock
import unittest2

from robottelo.cli.base import Base


class CLIClass(Base):
    """Class used for the username and password lookup tests"""
    foreman_admin_username = 'adminusername'
    foreman_admin_password = 'adminpassword'


class BaseCliTestCase(unittest2.TestCase):
    """Tests for the Base cli class"""

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

    @mock.patch('robottelo.cli.base.settings')
    def test_username_password_config_lookup(self, settings):
        """Username and password returned are from configuration"""
        settings.server.username = 'alice'
        settings.server.password = 'hackme'
        username, password = Base._get_username_password()

        self.assertEqual(username, settings.server.username)
        self.assertEqual(password, settings.server.password)

    def test_with_user(self):
        """Check if ``with_user`` method returns a right wrapper class"""
        new_class = Base.with_user('auser', 'apass')

        self.assertEqual(new_class.foreman_admin_username, 'auser')
        self.assertEqual(new_class.foreman_admin_password, 'apass')
        self.assertIn(Base, new_class.__bases__)
