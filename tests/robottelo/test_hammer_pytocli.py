# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import pytest

from robottelo.cli.base import CLIReturnCodeError, CLIDataBaseError
from robottelo.cli.hammer_pytocli import (
    execute_pytocli_cmd, execute_hammer_raw, check_errors, Hammer,
    SettingsListCmd, SettingsSetCmd, OrganizationCmd, OrganizationListCmd
)
from robottelo.ssh import SSHCommandResult

_HAMMER_LIST_STDOUT = '''[
    {
        "Id": 1,
        "Title": "Default Organization",
        "Name": "Default Organization",
        "Description": null,
        "Label": "Default_Organization"
    }
]
'''
_HAMMER_LIST_RESULT = SSHCommandResult(
    stdout=_HAMMER_LIST_STDOUT,
    stderr='', return_code=0, output_format=u'plain')


@pytest.fixture
def settings_mock(mocker):
    config = {
        'settings.locale': 'en_US.UTF-8',
        'settings.performance.time_hammer': False,
        'settings.server.admin_username': 'admin',
        'settings.server.admin_password': 'password',
    }
    config_module_mock = mocker.patch(
        'robottelo.cli.hammer_pytocli.base.config', **config)
    config_module_mock.start()
    return config_module_mock.settings


@pytest.fixture
def command_mock(mocker, settings_mock):
    config = {'command.return_value': _HAMMER_LIST_RESULT}
    ssh_mock = mocker.patch('robottelo.cli.hammer_pytocli.base.ssh', **config)
    ssh_mock.start()
    return ssh_mock.command


@pytest.fixture
def warning_mock(mocker):
    logger_warning_mock = mocker.patch(
        'robottelo.cli.hammer_pytocli.base.logger.warning')
    logger_warning_mock.start()
    return logger_warning_mock


@pytest.fixture
def execute_pytocli_mock(mocker, settings_mock):
    exec_function_mock = mocker.patch(
        'robottelo.cli.hammer_pytocli.base.execute_pytocli_cmd')
    exec_function_mock.start()
    return exec_function_mock


def test_hammer():
    assert 'hammer' == str(Hammer())


def test_hammer_help():
    assert 'hammer --help' == str(Hammer().help())


def test_hammer_doc():
    assert 'Option --help: show help msg for hammer command' == repr(
        Hammer.help)


@pytest.mark.parametrize('cmd', [OrganizationCmd(), Hammer().organization])
def test_hammer_organization(cmd):
    assert 'hammer organization' == str(cmd)


def test_organization_in_verbose_mode_from_hammer():
    assert 'hammer -v organization' == str(Hammer().verbose().organization)


def test_organization_in_verbose_mode_hammer_property():
    org_cmd = OrganizationCmd()
    org_cmd.hammer.verbose()
    assert 'hammer -v organization' == str(org_cmd)


def test_organization_in_verbose_mode_parent_cmd_property():
    org_cmd = OrganizationCmd()
    org_cmd.parent_cmd.verbose()
    assert 'hammer -v organization' == str(org_cmd)


def test_organization_list_with_multiple_hammer_options():
    assert 'hammer -v -u foo -p abc123 organization list' == str(
        Hammer().verbose().username('foo').password(
            u'abc123').organization.list)


def test_organization_list_with_multiple_hammer_options_property():
    org_list_cmd = OrganizationListCmd()
    org_list_cmd.hammer.verbose().username('foo').password('abc123')
    assert 'hammer -v -u foo -p abc123 organization list' == str(org_list_cmd)


def test_organization_list_with_multiple_hammer_options_parent_cmd():
    org_list_cmd = OrganizationListCmd()
    org_list_cmd.parent_cmd.parent_cmd.verbose().username('foo').password(
        'abc123')
    assert 'hammer -v -u foo -p abc123 organization list' == str(org_list_cmd)


def test_settings_set_name_and_value():
    assert 'hammer settings set --name send_welcome_email --value true' == str(
        SettingsSetCmd().name_option('send_welcome_email').value('true'))


def test_settings_list():
    assert 'hammer settings list' == str(SettingsListCmd())


def test_executed_pytocli_cmd_result(command_mock):
    result = execute_pytocli_cmd(Hammer().output('json').organization.list)
    assert result is command_mock.return_value


def test_executed_pytocli_default_parameters(command_mock):
    cmd = Hammer().output('json').organization.list
    execute_pytocli_cmd(cmd)
    command_mock.assert_called_once_with(
        'LANG=en_US.UTF-8 hammer --output json organization list'.encode(
            'utf8'),
        timeout=None,
        connection_timeout=None,
        output_format='plain'
    )


def test_executed_pytocli_non_default_parameters(command_mock, settings_mock):
    cmd = Hammer().output('json').organization.list
    settings_mock.locale = 'pt_BR.UTF-8'
    settings_mock.performance.time_hammer = True
    execute_pytocli_cmd(cmd, timeout=1, connection_timeout=2)
    command_mock.assert_called_once_with(
        'LANG=pt_BR.UTF-8 time -p hammer --output json organization '
        'list'.encode(
            'utf8'),
        timeout=1,
        connection_timeout=2,
        output_format='plain'
    )


def test_execute_hammer_raw_parameters(execute_pytocli_mock):
    cmd = Hammer().output('json').organization.list
    execute_hammer_raw(cmd, timeout=1, connection_timeout=2)
    execute_pytocli_mock.assert_called_once_with(cmd, 1, 2, )


@pytest.mark.usefixtures('execute_pytocli_mock')
def test_execute_hammer_raw_settings_credentials():
    cmd = Hammer().output('json').organization.list
    execute_hammer_raw(cmd)
    expected = 'hammer --output json -u admin -p password organization list'
    msg = 'credentials from settings should be included on command'
    assert expected == str(cmd), msg


@pytest.mark.usefixtures('execute_pytocli_mock')
def test_execute_hammer_raw_overridden_credentials():
    cmd = Hammer().output('json').username('foo').password(
        'bar').organization.list
    execute_hammer_raw(cmd)
    expected = 'hammer --output json -u foo -p bar organization list'
    msg = 'credentials from command should override settings credentials'
    assert expected == str(cmd), msg


def test_positive_check_errors(warning_mock):
    check_errors(Hammer(), _HAMMER_LIST_RESULT)
    assert warning_mock.call_count == 0


def test_check_errors_stderr(warning_mock):
    result = SSHCommandResult(
        stdout=_HAMMER_LIST_STDOUT,
        stderr='something', return_code=0, output_format=u'plain')
    check_errors(Hammer(), result)
    warning_mock.called_once_with(
        'stderr contains following message:\nsomething')


def test_check_errors_ignore_stderr(warning_mock):
    result = SSHCommandResult(
        stdout=_HAMMER_LIST_STDOUT,
        stderr='something', return_code=0, output_format=u'plain')
    check_errors(Hammer(), result, ignore_stderr=True)
    assert warning_mock.call_count == 0


@pytest.mark.parametrize(
    'stderr', ['INSERT INTO', 'SELECT * FROM', 'violates foreign key'])
def test_check_errors_db_error(stderr):
    result = SSHCommandResult(
        stdout=None,
        stderr=stderr, return_code=1, output_format=u'plain')
    with pytest.raises(CLIDataBaseError) as cli_error:
        check_errors(Hammer(), result)
    exception = cli_error.value
    assert (1, stderr) == (exception.return_code, exception.stderr)


def test_check_errors_return_code_error():
    result = SSHCommandResult(
        stdout=None,
        stderr='error', return_code=2, output_format=u'plain')
    with pytest.raises(CLIReturnCodeError) as cli_error:
        check_errors(Hammer(), result)
    exception = cli_error.value
    assert (2, 'error') == (exception.return_code, exception.stderr)


list_json_cmd = OrganizationListCmd()
list_json_cmd.hammer.output('json')


@pytest.mark.parametrize('cmd', [OrganizationListCmd(), list_json_cmd])
@pytest.mark.usefixtures('command_mock')
def test_execute_json_reinforcement(cmd):
    cmd.execute()
    assert (
        'hammer --output json -u admin -p password organization list' ==
        str(cmd)
    )


@pytest.mark.usefixtures('command_mock')
def test_execute_hammer():
    parsed = OrganizationCmd().execute()
    assert parsed == [
        {
            u'id': u'1', u'title': u'Default Organization',
            u'label': u'Default_Organization', u'description': None,
            u'name': u'Default Organization'
        }
    ]
