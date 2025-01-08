"""
Usage::

    hammer bootdisk [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    Subcommand
    [ARG] ...                     Subcommand arguments

Subcommands::

    generic                       Download generic image
    host                          Download host image
    subnet                        Download subnet generic image
"""

from robottelo.cli.base import Base


class Bootdisk(Base):
    """Manipulates Bootdisk."""

    command_base = 'bootdisk'

    @classmethod
    def generic(cls, options=None):
        """Download generic image"""
        cls.command_sub = 'generic'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def host(cls, options=None):
        """Download host image"""
        cls.command_sub = 'host'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def subnet(cls, options=None):
        """Download subnet generic image"""
        cls.command_sub = 'subnet'
        return cls.execute(cls._construct_command(options), output_format='json')
