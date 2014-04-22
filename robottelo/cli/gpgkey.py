# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer gpg [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List GPG Keys
    info                          Show a GPG key
    create                        Create a GPG Key
    update                        Update a GPG Key
    delete                        Destroy a GPG Key
"""

from robottelo.cli.base import Base


class GPGKey(Base):
    """
    Manipulates Foreman's GPG Keys.
    """

    command_base = "gpg"
    command_requires_org = True

    @classmethod
    def info(cls, options=None):
        """
        Gets information for GPG Key
        """

        cls.command_sub = "info"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        # Need to rebuild the returned object
        # First check for content key
        # id, name, content, organization, repositories

        if len(result.stdout) > 0:
            key_record = {}

            # First item should contain most fields
            key_record = result.stdout.pop(0)
            if 'organization' not in key_record:
                raise ValueError('Could not find GPG Key')

            # Remaining items belong to content

            for item in result.stdout:
                for key, val in item.items():
                    key_record['content'] += val
            # Update stdout with dictionary
            result.stdout = key_record

        return result
