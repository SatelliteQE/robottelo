import six
import unittest2

from robottelo.cli.base import (
    Base,
    CLIReturnCodeError,
    CLIError,
    CLIBaseError,
    CLIDataBaseError
)

if six.PY2:
    import mock
else:
    from unittest import mock


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
        settings.server.admin_username = 'alice'
        settings.server.admin_password = 'hackme'
        username, password = Base._get_username_password()

        self.assertEqual(username, settings.server.admin_username)
        self.assertEqual(password, settings.server.admin_password)

    def test_with_user(self):
        """Check if ``with_user`` method returns a right wrapper class"""
        new_class = Base.with_user('auser', 'apass')

        self.assertEqual(new_class.foreman_admin_username, 'auser')
        self.assertEqual(new_class.foreman_admin_password, 'apass')
        self.assertIn(Base, new_class.__bases__)

    def test_handle_response_success(self):
        """Check handle_response returns stdout when the is no problem on ssh
        execution
        """
        base = Base()
        response = mock.Mock()
        response.return_code = 0
        response.stderr = []
        self.assertEqual(response.stdout, base._handle_response(response))

    @mock.patch('robottelo.cli.base.Base.logger.warning')
    def test_handle_response_logging_when_stderr_not_empty(self, warning):
        """Check handle_response log stderr when it is not empty"""
        base = Base()
        response = mock.Mock()
        response.return_code = 0
        response.stderr = [u'not empty']
        self.assertEqual(response.stdout, base._handle_response(response))
        warning.assert_called_once_with(
            u'stderr contains following message:\n{}'.format(response.stderr)
        )
        warning.reset_mock()
        self.assertEqual(
            response.stdout,
            base._handle_response(response, True)
        )
        self.assertFalse(
            warning.called,
            u'Should not be called when ignore_stderr is True'
        )

    def test_handle_response_error(self):
        """Check handle_response raise ``CLIReturnCodeError`` when
        return_code is not 0
        """
        self.assert_response_error(CLIReturnCodeError)

    def test_handle_data_base_response_error(self):
        """Check handle_response raise ``CLIDataBaseError`` when
        return_code is not 0 and error is related to DB error.
        See https://github.com/SatelliteQE/robottelo/issues/3790.
        """
        msgs = (
            '''SELECT  "filters"."id" AS t0_r0, "filters"."search" AS t0_r1,
            "filters"."role_id" AS t0_r2, "filters"."created_at" AS t0_r3,
            "filters"."updated_at" AS t0_r4, "filters"."taxonomy_search" AS
            t0_r5, "roles"."id" AS t1_r0, "roles"."name" AS t1_r1,
            "roles"."builtin" AS t1_r2, "roles"."permissions" AS t1_r3 FROM
            "filters" LEFT OUTER JOIN "roles" ON "roles"."id" =
            "filters"."role_id" WHERE (("roles"."id" = '')) ORDER BY role_id,
            filters.id LIMIT 20 OFFSET 0
            ''',
            '''INSERT INTO "katello_subscriptions" ("cp_id", "created_at",
            "updated_at") VALUES ($1, $2, $3) RETURNING "id"
            ''',
            '''Could not create the hostgroup:
              ERROR:  insert or update on table "hostgroups"
              violates foreign key
              constraint "hostgroups_architecture_id_fk"
              DETAIL:  Key (architecture_id)=(1122222) is not present in table
              "architectures"
            '''
        )
        for msg in msgs:
            self.assert_response_error(CLIDataBaseError, msg)

    def assert_response_error(self, expected_error, stderr=u'some error'):
        """Check error is raised when handling cli response
        :param expected_error: expected error (class)
        :param stderr: error present on stderr (str)
        :return:
        """
        base = Base()
        response = mock.Mock()
        response.return_code = 1
        response.stderr = [stderr]
        self.assertRaises(expected_error, base._handle_response, response)

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_operating_system(self, construct, execute):
        """Check command_sub edited when executing add_operating_system"""
        options = {u'foo': u'bar'}
        self.assertNotEqual('add-operatingsystem', Base.command_sub)
        self.assertEqual(
            execute.return_value,
            Base.add_operating_system(options)
        )
        self.assertEqual('add-operatingsystem', Base.command_sub)
        construct.called_once_with(options)
        execute.called_once_with(construct.return_value)

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_create_with_empty_result(self, construct, execute):
        """Check command create when result is empty"""
        execute.return_value = []
        self.assertEqual(
            execute.return_value,
            Base.create()
        )
        self.assertEqual('create', Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(construct.return_value, output_format='csv')

    @mock.patch('robottelo.cli.base.Base.info')
    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_create_with_result_dct_without_id(
            self, construct, execute, info):
        """Check command create when result has dct but dct hasn't id key"""
        execute.return_value = [{'not_id': 'foo'}]
        self.assertEqual(
            execute.return_value,
            Base.create()
        )
        self.assertEqual('create', Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(construct.return_value, output_format='csv')
        self.assertFalse(info.called)

    @mock.patch('robottelo.cli.base.Base.info')
    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_create_with_result_dct_with_id_not_required_org(
            self, construct, execute, info):
        """Check command create when result has dct id key and organization
        is not required
        """
        execute.return_value = [{'id': 'foo', 'bar': 'bas'}]
        Base.command_requires_org = False
        self.assertEqual(
            execute.return_value,
            Base.create()
        )
        self.assertEqual('create', Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(construct.return_value, output_format='csv')
        info.called_once_with({'id': 'foo'})

    @mock.patch('robottelo.cli.base.Base.info')
    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_create_with_result_dct_with_id_required_org(
            self, construct, execute, info):
        """Check command create when result has dct id key and organization
        is required
        """
        execute.return_value = [{'id': 'foo', 'bar': 'bas'}]
        Base.command_requires_org = True
        self.assertEqual(
            execute.return_value,
            Base.create({'organization-id': 'org-id'})
        )
        self.assertEqual('create', Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(construct.return_value, output_format='csv')
        info.called_once_with({'id': 'foo', 'organization-id': 'org-id'})

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_add_create_with_result_dct_id_required_org_error(
            self, construct, execute):
        """Check command create when result has dct id key and organization
        is required but is not present
        """
        execute.return_value = [
            {'id': 'foo', 'bar': 'bas'}
        ]
        Base.command_requires_org = True
        self.assertRaises(CLIError, Base.create)
        self.assertEqual('create', Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(construct.return_value, output_format='csv')

    def assert_cmd_execution(
            self, construct, execute, base_method, cmd_sub,
            ignore_stderr=False):
        """Asssert Base class method successfully executed """
        self.assertEquals(execute.return_value, base_method())
        self.assertEqual(cmd_sub, Base.command_sub)
        construct.called_once_with({})
        execute.called_once_with(
            construct.return_value, ignore_stderr=ignore_stderr
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_delete(self, construct, execute):
        """Check delete method"""
        self.assert_cmd_execution(
            construct, execute, Base.delete, 'delete', True)

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_delete_parameter(self, construct, execute):
        """Check delete_parameter method"""
        self.assert_cmd_execution(
            construct, execute, Base.delete_parameter, 'delete-parameter')

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_dump(self, construct, execute):
        """Check dump method"""
        self.assert_cmd_execution(construct, execute, Base.dump, 'dump')


class CLIErrorTests(unittest2.TestCase):
    """Tests for the CLIError cli class"""

    def test_error_msg_is_exposed(self):
        """Check if message error is exposed to assertRaisesRegexp"""
        msg = u'organization-id option is required for Foo.create'
        with self.assertRaisesRegexp(CLIError, msg):
            raise CLIError(msg)


class CLIBaseErrorTestCase(unittest2.TestCase):
    """Tests for the CLIReturnCodeError cli class"""

    def test_init(self):
        """Check properties initialization"""
        error = CLIBaseError(1, u'stderr', u'msg')
        self.assertEqual(error.return_code, 1)
        self.assertEqual(error.stderr, u'stderr')
        self.assertEqual(error.msg, u'msg')
        self.assertEqual(error.message, error.msg)

    def test_return_code_is_exposed(self):
        """Check if return_code is exposed to assertRaisesRegexp"""
        with self.assertRaisesRegexp(CLIBaseError, u'1'):
            raise CLIBaseError(1, u'stderr', u'msg')

    def test_stderr_is_exposed(self):
        """Check if stderr is exposed to assertRaisesRegexp"""
        with self.assertRaisesRegexp(CLIBaseError, u'stderr'):
            raise CLIBaseError(1, u'stderr', u'msg')

    def test_message_is_exposed(self):
        """Check if message is exposed to assertRaisesRegexp"""
        with self.assertRaisesRegexp(CLIBaseError, u'msg'):
            raise CLIBaseError(1, u'stderr', u'msg')
