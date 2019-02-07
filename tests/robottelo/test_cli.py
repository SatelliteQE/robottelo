import six
import unittest2

from functools import partial
from robottelo.cli.base import (
    Base,
    CLIBaseError,
    CLIDataBaseError,
    CLIError,
    CLIReturnCodeError
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
            ignore_stderr=False, **base_method_kwargs):
        """Asssert Base class method successfully executed """
        self.assertEqual(
            execute.return_value,
            base_method(**base_method_kwargs)
        )
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

    @mock.patch('robottelo.cli.base.ssh.command')
    @mock.patch('robottelo.cli.base.settings')
    def test_execute_with_raw_response(self, settings, command):
        """Check excuted build ssh method and returns raw response"""
        settings.locale = 'en_US'
        settings.performance = False
        settings.server.admin_username = 'admin'
        settings.server.admin_password = 'password'
        response = Base.execute('some_cmd', return_raw_response=True)
        ssh_cmd = u'LANG=en_US  hammer -v -u admin -p password  some_cmd'
        command.assert_called_once_with(
            ssh_cmd.encode('utf-8'),
            output_format=None,
            timeout=None,
            connection_timeout=None
        )
        self.assertIs(response, command.return_value)

    @mock.patch('robottelo.cli.base.Base._handle_response')
    @mock.patch('robottelo.cli.base.ssh.command')
    @mock.patch('robottelo.cli.base.settings')
    def test_execute_with_performance(self, settings, command, handle_resp):
        """Check excuted build ssh method and delegate response handling"""
        settings.locale = 'en_US'
        settings.performance.timer_hammer = True
        settings.server.admin_username = 'admin'
        settings.server.admin_password = 'password'
        response = Base.execute('some_cmd', output_format='json')
        ssh_cmd = (
            u'LANG=en_US time -p hammer -v -u admin -p password --output=json'
            u' some_cmd'
        )
        command.assert_called_once_with(
            ssh_cmd.encode('utf-8'),
            output_format='json',
            timeout=None,
            connection_timeout=None
        )
        handle_resp.assert_called_once_with(
            command.return_value,
            ignore_stderr=None
        )
        self.assertIs(response, handle_resp.return_value)

    @mock.patch('robottelo.cli.base.Base.list')
    def test_exists_without_option_and_empty_return(self, lst_method):
        """Check exists method without options and empty return"""
        lst_method.return_value = []
        response = Base.exists(search=['id', 1])
        lst_method.assert_called_once_with({u'search': u'id=\\"1\\"'})
        self.assertEqual([], response)

    @mock.patch('robottelo.cli.base.Base.list')
    def test_exists_with_option_and_no_empty_return(self, lst_method):
        """Check exists method with options and no empty return"""
        lst_method.return_value = [1, 2]
        my_options = {u'search': u'foo=bar'}
        response = Base.exists(my_options, search=['id', 1])
        lst_method.assert_called_once_with(my_options)
        self.assertEqual(1, response)

    @mock.patch('robottelo.cli.base.Base.command_requires_org')
    def test_info_requires_organization_id(self, _):
        """Check info raises CLIError with organization-id is not present in
        options
        """
        self.assertRaises(CLIError, Base.info)

    @mock.patch('robottelo.cli.base.hammer.parse_info')
    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_info_without_parsing_response(self, construct, execute, parse):
        """Check info method execution without parsing response"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.info,
            'info',
            output_format='json',
            options={'organization-id': 1}
        )
        parse.assert_not_called()

    @mock.patch('robottelo.cli.base.hammer.parse_info')
    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_info_parsing_response(self, construct, execute, parse):
        """Check info method execution parsing response"""
        parse.return_value = execute.return_value = 'some_response'
        self.assert_cmd_execution(
            construct,
            execute,
            Base.info,
            'info',
            options={'organization-id': 1}
        )
        parse.called_once_with('some_response')

    @mock.patch('robottelo.cli.base.Base.command_requires_org')
    def test_list_requires_organization_id(self, _):
        """Check list raises CLIError with organization-id is not present in
        options
        """
        self.assertRaises(CLIError, Base.list)

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_list_with_default_per_page(self, construct, execute):
        """Check list method set per_page as 1000 by default"""
        self.assertEqual(
            execute.return_value,
            Base.list(options={'organization-id': 1})
        )
        self.assertEqual('list', Base.command_sub)
        construct.called_once_with({'per-page': 1000})
        execute.called_once_with(construct.return_value, output_format='csv')

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_list_without_per_page(self, construct, execute):
        """Check list with per_page set as false"""
        list_with_per_page_false = partial(
            Base.list,
            per_page=False,
            options={'organization-id': 1}
        )
        self.assert_cmd_execution(
            construct,
            execute,
            list_with_per_page_false,
            'list',
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_puppet_classes(self, construct, execute):
        """Check puppet_classes method execution"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.puppetclasses,
            'puppet-classes'
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_remove_operating_system(self, construct, execute):
        """Check remove_operating_system method execution"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.remove_operating_system,
            'remove-operatingsystem'
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_sc_params(self, construct, execute):
        """Check sc_params method execution"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.sc_params,
            'sc-params'
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_set_parameter(self, construct, execute):
        """Check set_parameter method execution"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.set_parameter,
            'set-parameter'
        )

    @mock.patch('robottelo.cli.base.Base.execute')
    @mock.patch('robottelo.cli.base.Base._construct_command')
    def test_update(self, construct, execute):
        """Check update method execution"""
        self.assert_cmd_execution(
            construct,
            execute,
            Base.update,
            'update'
        )


class CLIErrorTests(unittest2.TestCase):
    """Tests for the CLIError cli class"""

    def test_error_msg_is_exposed(self):
        """Check if message error is exposed to assertRaisesRegex"""
        msg = u'organization-id option is required for Foo.create'
        with self.assertRaisesRegex(CLIError, msg):
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
        """Check if return_code is exposed to assertRaisesRegex"""
        with self.assertRaisesRegex(CLIBaseError, u'1'):
            raise CLIBaseError(1, u'stderr', u'msg')

    def test_stderr_is_exposed(self):
        """Check if stderr is exposed to assertRaisesRegex"""
        with self.assertRaisesRegex(CLIBaseError, u'stderr'):
            raise CLIBaseError(1, u'stderr', u'msg')

    def test_message_is_exposed(self):
        """Check if message is exposed to assertRaisesRegex"""
        with self.assertRaisesRegex(CLIBaseError, u'msg'):
            raise CLIBaseError(1, u'stderr', u'msg')
