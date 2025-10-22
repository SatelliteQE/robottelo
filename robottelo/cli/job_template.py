"""
Usage:
    hammer job-template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:

    SUBCOMMAND      subcommand
    [ARG] ...       subcommand arguments

Subcommands:

     create         Create a job template
     delete         Delete a job template
     dump           View job template content
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
