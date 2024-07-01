"""
Usage::

    scap-content [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

     SUBCOMMAND                    subcommand
     [ARG] ...                     subcommand arguments

Subcommands::

     create                        Create SCAP content
     delete                        Deletes an SCAP content
     info                          Show an SCAP content
     list                          List SCAP contents
     update                        Update an SCAP content
"""

from robottelo.cli.base import Base


class Scapcontent(Base):
    """Manipulates Satellite's scap-content."""

    command_base = 'scap-content'
