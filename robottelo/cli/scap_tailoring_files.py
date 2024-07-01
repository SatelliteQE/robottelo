"""
Usage::

     tailoring-file [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

     SUBCOMMAND                    subcommand
     [ARG] ...                     subcommand arguments

Subcommands::

     create                        Create a Tailoring file
     delete                        Deletes a Tailoring file
     download                      Show a Tailoring file as XML
     info                          Show a Tailoring file
     list                          List Tailoring files
     update                        Update a Tailoring file
"""

from robottelo.cli.base import Base


class TailoringFiles(Base):
    """Manipulates Satellite's tailoring-file."""

    command_base = 'tailoring-file'

    @classmethod
    def download_tailoring_file(cls, options):
        """Downloads the tailoring file from satellite"""
        cls.command_sub = 'download'
        return cls.execute(cls._construct_command(options), output_format='table')
