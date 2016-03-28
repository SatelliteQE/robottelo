# -*- encoding: utf-8 -*-
"""
Usage::

    hammer content-host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    available-incremental-updates Given a set of systems and errata, lists the
                                  content view versions and environments that
                                  need updating.
    create                        Register a content host
    delete                        Unregister a content host
    info                          Show a content host
    list                          List content hosts
    tasks
    update                        Update content host information

"""
from robottelo.cli.base import Base


class ContentHost(Base):
    """Manipulates Katello engine's content-host command."""
    command_base = 'content-host'

    @classmethod
    def tasks(cls, options=None):
        """Lists async tasks for a content host."""
        cls.command_sub = 'tasks'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
