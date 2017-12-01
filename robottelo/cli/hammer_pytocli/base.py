# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from logging import Logger

import re
from pytocli import (
    SubCommand, CommandBuilder, Option, NoValueOption,
    SingleValueOption, SubCommandBuilder
)

from robottelo import config, ssh
from robottelo.cli.base import CLIDataBaseError, CLIReturnCodeError
from robottelo.cli.hammer import parse_json

_DB_ERROR_REGEX = re.compile(
    r'.*INSERT INTO|.*SELECT .*FROM|.*violates foreign key'
)

logger = Logger(__file__)


def execute_pytocli_cmd(cmd, timeout=None, connection_timeout=None):
    """Executes a pytocli command on server

    :param cmd: pytocli.CommandBuilder
    :param timeout: int for timeout
    :param connection_timeout: int for connection timetout
    :return: SSHCommandResult
    """

    time_hammer = False
    if config.settings.performance:
        time_hammer = config.settings.performance.time_hammer
    cmd_prefix = 'LANG={}'.format(config.settings.locale)
    # add time to measure hammer performance
    if time_hammer:
        cmd_prefix += ' time -p'
    ssh_cmd = '{prefix} {cmd!s}'.format(prefix=cmd_prefix, cmd=cmd)
    return ssh.command(
        ssh_cmd.encode('utf-8'),
        timeout=timeout,
        connection_timeout=connection_timeout,
        output_format='plain'
    )


def execute_hammer_raw(cmd, timeout=None, connection_timeout=None):
    """Execute HammerSubCommand using ssh. Errors on result are not handled,
    the raw result is returned instead.
    Use execute_hammer for a high level version, where error are handled and
    output is parsed

    :param cmd: HammerSubCommand
    :param timeout: int for timeout
    :param connection_timeout: int for connection timetout
    :return: SSHCommandResult
    """
    try:
        cmd.hammer.username(config.settings.server.admin_username)
    except ValueError:
        pass  # cmd has already defined username

    try:
        cmd.hammer.password(config.settings.server.admin_password)
    except ValueError:
        pass  # cmd has already defined username
    return execute_pytocli_cmd(cmd, timeout, connection_timeout)


def check_errors(cmd, response, ignore_stderr=False):
    if response.return_code != 0:
        full_msg = (
            u'Command "{cmd}" finished with return_code {return_code}\n'
            'stderr contains following message:\n{error}'.format(
                cmd=cmd,
                return_code=response.return_code,
                error=response.stderr
            )
        )
        error_data = (response.return_code, response.stderr, full_msg)
        if _DB_ERROR_REGEX.search(full_msg):
            raise CLIDataBaseError(*error_data)
        raise CLIReturnCodeError(*error_data)
    if len(response.stderr) != 0 and not ignore_stderr:
        logger.warning(
            u'stderr contains following message:\n{error}'.format(
                error=response.stderr
            )
        )


class AddSubCommandMixin(object):
    @classmethod
    def add_subcommand(cls, subcommand_cls):
        subcommand_cls._parent_cmd_factory = cls
        descriptor = SubCommand(subcommand_cls)
        descriptor._set_cmd_attr_name(subcommand_cls.name)
        setattr(cls, subcommand_cls.name, descriptor)
        sub_commands = list(cls.sub_commands)
        sub_commands.append(subcommand_cls.name)
        cls.sub_commands = tuple(sub_commands)
        return subcommand_cls


class SSHExecutionMixin(object):
    def execute(self, timeout=None, connection_timeout=None,
                ignore_stderr=None):
        """Execute Hammer sub commands and parses output. Command must define
            json format. If output not present, output will be added to it.

            :param timeout: int for timeout
            :param connection_timeout: int for connection timeout
            :param ignore_stderr: If not False content present on stderr
            will be logged
            :return: parsed stdout
            """
        try:
            self.hammer.output('json')
        except ValueError:
            pass  # format already fetched
        response = execute_hammer_raw(self, timeout, connection_timeout)
        check_errors(self, response, ignore_stderr)
        return parse_json(response.stdout)


class Hammer(AddSubCommandMixin, SSHExecutionMixin, CommandBuilder):
    """Base parent class hammer"""
    name = u'hammer'
    help = Option(
        NoValueOption, u'--help', doc=u'show help msg for hammer command')
    debug = Option(
        NoValueOption, u'-d', doc=u'run hammer in debug mode')
    username = Option(
        SingleValueOption, u'-u', doc=u'username to access the remote system')
    password = Option(
        SingleValueOption, u'-p', doc=u'password to access the remote system')
    verbose = Option(
        NoValueOption, u'-v', doc=u'runs hammer in verbose mode')
    output = Option(
        SingleValueOption,
        u'--output',
        doc=u'Set output format. One of [base, table, silent, csv, yaml, json]'
    )

    @property
    def hammer(self):
        return self


class UndefinedParentCommand(Exception):
    pass


class HammerSubCommand(AddSubCommandMixin, SSHExecutionMixin,
                       SubCommandBuilder):
    """Base class for hammer sub commands. Check OrganizationCmd as
    example
    """

    _parent_cmd_factory = None

    @property
    def hammer(self):
        current = self.parent_cmd
        while isinstance(current, SubCommandBuilder):
            current = current.parent_cmd

        return current

    def __init__(self, parent_cmd=None):
        if parent_cmd is None:
            if self._parent_cmd_factory is None:
                raise UndefinedParentCommand(
                    u'{cls} has not parent factory. Use a Hammer or '
                    u'HammerSubCommand class method add_subcommand decorator '
                    u'to fix this'.format(cls=type(self))
                )
            parent_cmd = self._parent_cmd_factory()
        super(HammerSubCommand, self).__init__(parent_cmd)
