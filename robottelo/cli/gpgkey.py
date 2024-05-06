"""
Usage::

    hammer gpg [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a GPG Key
    delete                        Destroy a GPG Key
    info                          Show a GPG key
    list                          List GPG Keys
    update                        Update a GPG Key
"""

from robottelo.cli.base import Base


class GPGKey(Base):
    """
    Manipulates Foreman's GPG Keys.
    """

    command_base = 'gpg'
    command_requires_org = True

    @classmethod
    def info(cls, options=None):
        """
        Gets information for GPG Key
        """

        cls.command_sub = 'info'

        return cls.execute(cls._construct_command(options), output_format='json')
