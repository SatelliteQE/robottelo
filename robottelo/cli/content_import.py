"""
Usage::

    hammer content-import [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    library                       Imports a content archive to an organization's library
                                  lifecycle environment
    list                          View content view import histories
    version                       Imports a content archive to a content view version

"""
from robottelo.cli.base import Base


class ContentImport(Base):
    """
    Import content to satellite
    """

    command_base = 'content-import'
    command_requires_org = True

    @classmethod
    def list(cls, options=None):
        """
        List previous imports
        """
        cls.command_sub = 'list'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def library(cls, options, timeout=None):
        """
        Make library import
        """
        cls.command_sub = 'library'
        return cls.execute(cls._construct_command(options), output_format='json', timeout=timeout)

    @classmethod
    def version(cls, options, timeout=None):
        """
        Make CV version export
        """
        cls.command_sub = 'version'
        return cls.execute(cls._construct_command(options), output_format='json', timeout=timeout)
