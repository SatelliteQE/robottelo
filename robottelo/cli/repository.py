# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer repository [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a repository
    delete                        Destroy a repository
    info                          Show a repository
    list                          List of repositories
    synchronize                   Sync a repository
    update                        Update a repository
"""

from robottelo.cli.base import Base


class Repository(Base):
    """
    Manipulates Katello engine's repository command.
    """

    command_base = "repository"

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available repositories.
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def synchronize(cls, options):
        """
        Synchronizes a repository.
        """

        cls.command_sub = "synchronize"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def info_ng(cls, options):
        """
        Override Base class method
        """
        cls.command_sub = "info"

        result = cls.execute(cls._construct_command(options), expect_csv=False)

        r = dict()
        for x in result.stdout:
            if x == '':
                continue
            if x.startswith("    "):
                [key, value] = x.strip().split(":", 1)
                r[last_key][key.strip().replace(' ', '-').lower()] = value.strip()
            else:
                [key, value] = x.strip().split(":", 1)
                if value.strip() == '':
                    last_key = key.strip().replace(' ', '-').lower()
                    r[last_key] = dict()
                else:
                    r[key.strip().replace(' ', '-').lower()] = value.strip()
        result.stdout = r
        return result
