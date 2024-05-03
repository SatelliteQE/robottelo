"""
Usage::

    hammer remote-execution-feature [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND      Subcommand
    [ARG] ...       Subcommand arguments

Subcommands::

    info            Show remote execution feature
    list            List remote execution features
    update          Update a job template

"""

from robottelo.cli.base import Base


class RemoteExecutionFeature(Base):
    """
    Handles Remote Execution Feature commands
    """

    command_base = 'remote-execution-feature'
