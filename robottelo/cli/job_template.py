"""
Usage:
    hammer job-template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:

    SUBCOMMAND      subcommand
    [ARG] ...       subcommand arguments

Subcommands:

     clone          Clone a provision template
     create         Create a job template
     delete         Delete a job template
     dump           View job template content
     export         Export a template including all metadata
     import         Import a job template from ERB
     info           Show job template details
     list           List job templates
     update         Update a job template
"""

from robottelo.cli.base import Base


class JobTemplate(Base):
    """
    Manipulate job templates.
    """

    command_base = 'job-template'

    @classmethod
    def export(cls, options, timeout=None):
        """Export a job template
        Specify at least --name or --id
        """
        cls.command_sub = 'export'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def import_template(cls, options, timeout=None):
        """Import a job template
        Specify at least  --file
        """
        cls.command_sub = 'import'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def clone(cls, options=None, output_format="json", timeout=None):
        """Clone a job template"""
        cls.command_sub = 'clone'
        return cls.execute(
            cls._construct_command(options), output_format=output_format, timeout=timeout
        )
