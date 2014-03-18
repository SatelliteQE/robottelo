# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer lifecycle-environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List environments in an organization
    update                        Update an environment
    create                        Create an environment
    delete                        Destroy an environment
    info                          Show an environment
"""

from robottelo.cli.base import Base


class LifecycleEnvironment(Base):
    """
    Manipulates Katello engine's lifecycle-environment command.
    """

    command_base = "lifecycle-environment"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def exists(cls, organization_id, tuple_search=None):
        """
        Search for a lifecycle environment.
        """

        # Katello subcommands require the organization-id
        options = {}

        if tuple_search:
            search_criteria = "%s:\"%s\"" % (tuple_search[0], tuple_search[1])
            options["search"] = search_criteria
        # Katello subcommands require extra arguments such as organization-id

        result = cls.list(organization_id, options)

        if result.stdout:
            result.stdout = result.stdout[0]

        return result

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available Lifecycle Environments for organization.
        """

        cls.command_sub = "list"

        if options is None:
            options = {}

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
