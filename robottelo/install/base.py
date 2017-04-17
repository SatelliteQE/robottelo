# -*- encoding: utf-8 -*-
"""Generic base class for install commands."""
import logging

from robottelo import ssh
from robottelo.config import conf


class InstallError(Exception):
    """Indicates that a install command could not be run."""


class Base(object):
    """
    @param command_base: base install command.
    """
    command_base = None  # each inherited instance should define this
    command_requires_auth = False  # True when command requires auth user
    command_service = None

    logger = logging.getLogger('robottelo')

    @classmethod
    def reset(cls, options=None):
        """
        dummy
        """

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options))
        return result

    @classmethod
    def execute(cls, command, user=None, password=None, timeout=None):
        """Executes  command on the server via ssh"""
        user, password = cls._get_username_password(user, password)

        # add time to measure hammer performance
        perf_test = conf.properties.get('performance.test.foreman.perf', '0')
        cmd = u'LANG={0} {1} {2}'.format(
            conf.properties['main.locale'],
            u'time -p' if perf_test == '1' else '',
            command,
        )

        return ssh.command(cmd.encode('utf-8'), timeout=timeout)

    @classmethod
    def service_restart(cls, options=None):
        """
        dummy
        """

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options))
        return result

    @classmethod
    def restore(cls, options=None):
        """dummy."""

        if options is None:
            options = {}

        if cls.command_requires_org and 'organization-id' not in options:
            raise InstallError(
                'organization-id option is required for {0}.info'
                .format(cls.__name__)
            )

        result = cls.execute(command=cls._construct_command(options))

        return result

    @classmethod
    def save(cls, options=None):
        """
        dummy.
        @param options
        """
        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def with_user(cls, username=None, password=None):
        """Context Manager for credentials"""
        if username is None:
            username = conf.properties['foreman.admin.username']
        if password is None:
            password = conf.properties['foreman.admin.password']

        class Wrapper(cls):
            """Wrapper class which defines the foreman admin username and
            password to be used when executing any cli command.

            """
            foreman_admin_username = username
            foreman_admin_password = password

        return Wrapper

    @classmethod
    def _construct_command(cls, options=None):
        """
        Build an install command based on the options passed
        """

        tail = u''

        if options is None:
            options = {}

        for key, val in options.items():
            if val is None:
                continue
            if val is True:
                tail += u' --{0}'.format(key)
            elif val is not False:
                if isinstance(val, list):
                    val = ','.join(str(el) for el in val)
                tail += u' --{0}="{1}"'.format(key, val)
        cmd = u'{0} {1}'.format(cls.command_base, tail.strip())

        return cmd

    @classmethod
    def _get_username_password(cls, username=None, password=None):
        """Lookup for the username and password in following order:
        1. ``user`` or ``password`` params
        2. ``foreman_admin_username`` or ``foreman_admin_password`` attributes
        3. foreman.admin.username or foreman.admin.password configuration

        :return: A tuple with the username and password found
        :rtype: tuple
        """
        if username is None:
            try:
                username = getattr(cls, 'foreman_admin_username')
            except AttributeError:
                username = conf.properties['foreman.admin.username']
        if password is None:
            try:
                password = getattr(cls, 'foreman_admin_password')
            except AttributeError:
                password = conf.properties['foreman.admin.password']

        return (username, password)
