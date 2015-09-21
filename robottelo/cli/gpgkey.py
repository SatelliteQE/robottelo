# -*- encoding: utf-8 -*-
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

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        # Need to rebuild the returned object
        # First check for content key
        # id, name, content, organization, repositories

        if len(result) > 0:

            # First item should contain most fields
            key_record = result.pop(0)
            if 'organization' not in key_record:
                raise ValueError('Could not find GPG Key')

            # Remaining items belong to content

            for item in result:
                for _, val in item.items():
                    key_record['content'] += val
            # Update result with dictionary
            result = key_record

        return result
