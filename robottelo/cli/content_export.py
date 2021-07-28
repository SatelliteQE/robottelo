"""
Usage::

    hammer content-export [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    complete                      Prepare content for a full export to a disconnected Katello
    generate-metadata             Writes export metadata to disk for use by the importing Katello.
                                  This command only needs to be used if the export was performed
                                  asynchronously or if the metadata was lost
    incremental                   Prepare content for an incremental export to a disconnected
                                  Katello
    list                          View content view export histories

"""
from robottelo.cli.base import Base


class ContentExport(Base):
    """
    Exports content from satellite
    """

    command_base = 'content-export'
    command_requires_org = True

    @classmethod
    def list(cls, options=None):
        """
        List previous exports
        """
        cls.command_sub = 'list'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def completeLibrary(cls, options):
        """
        Make full library export
        """
        cls.command_sub = 'complete library'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def completeVersion(cls, options):
        """
        Make full CV version export
        """
        cls.command_sub = 'complete version'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def incrementalLibrary(cls, options):
        """
        Make make incremental library export
        """
        cls.command_sub = 'incremental library'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def incrementalVersion(cls, options):
        """
        Make make incremental CV version export
        """
        cls.command_sub = 'incremental version'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def generateMetadata(cls, options):
        """
        Generates export metadata
        """
        cls.command_sub = 'generate-metadata'
        return cls.execute(cls._construct_command(options), output_format='json')
