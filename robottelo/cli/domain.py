"""
Usage::

    hammer domain [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a domain.
    delete                        Delete a domain.
    delete_parameter              Delete parameter for a domain.
    info                          Show a domain.
    list                          List of domains
    set_parameter                 Create or update parameter for a domain.
    update                        Update a domain.
"""

from robottelo.cli.base import Base


class Domain(Base):
    """
    Manipulates Foreman's domains.
    """

    command_base = 'domain'
