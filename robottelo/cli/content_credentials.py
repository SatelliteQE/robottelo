"""
Usage::

    hammer content-credential [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a content credential
    delete                        Destroy a content credential
    info                          Show a content credential
    list                          List content credentials
    update                        Update a content credential
"""

from robottelo.cli.base import Base


class ContentCredential(Base):
    """
    Manipulates Foreman's content credentials.
    """

    command_base = 'content-credential'
    command_requires_org = True

    @classmethod
    def info(cls, options=None):
        """
        Gets information for a content credential
        """

        cls.command_sub = 'info'

        return cls.execute(cls._construct_command(options), output_format='json')
