"""
Usage::

    hammer ostree-branch [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    info                          Show an ostree branch
    list                          List ostree_branches

"""

from robottelo.cli.base import Base


class OstreeBranch(Base):
    """Manipulates Ostree branches."""

    command_base = 'ostree-branch'
