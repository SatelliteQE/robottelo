# -*- encoding: utf-8 -*-
"""
Usage::

    hammer os [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-architecture              Associate a resource
    add-config-template           Associate a resource
    add-ptable                    Associate a resource
    create                        Create an OS.
    delete                        Delete an OS.
    delete-default-template
    delete-parameter              Delete parameter for an operating system.
    info                          Show an OS.
    list                          List all operating systems.
    remove-architecture           Disassociate a resource
    remove-config-template        Disassociate a resource
    remove-ptable                 Disassociate a resource
    set-default-template
    set-parameter                 Create or update parameter for an
                                  operating system.
    update                        Update an OS.
"""
from robottelo.cli.base import Base


class OperatingSys(Base):
    """
    Manipulates Foreman's operating systems.
    """

    command_base = 'os'

    @classmethod
    def add_architecture(cls, options=None):
        """
        Adds existing architecture to OS.
        """

        cls.command_sub = 'add-architecture'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def add_config_template(cls, options=None):
        """
        Adds existing template to OS.
        """

        cls.command_sub = 'add-config-template '

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def add_ptable(cls, options=None):
        """
        Adds existing partitioning table to OS.
        """

        cls.command_sub = 'add-ptable'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_architecture(cls, options=None):
        """
        Removes architecture from OS.
        """

        cls.command_sub = 'remove-architecture'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_config_template(cls, options=None):
        """
        Removes template from OS.
        """

        cls.command_sub = 'remove-config-template'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_ptable(cls, options=None):
        """
        Removes partitioning table from OS.
        """

        cls.command_sub = 'remove-ptable '

        result = cls.execute(cls._construct_command(options))

        return result
