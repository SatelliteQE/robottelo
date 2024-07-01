"""
Usage::

    hammer model [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a model.
    delete                        Delete a model.
    info                          Show a model.
    list                          List all models.
    update                        Update a model.
"""

from robottelo.cli.base import Base


class Model(Base):
    """
    Manipulates Foreman's hardware model.
    """

    command_base = 'model'
