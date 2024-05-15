"""
Usage:
    hammer virt-who-config [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a virt-who configuration
    delete                        Delete a virt-who configuration
    deploy                        Download and execute script for the specified
                                virt-who configuration
    fetch                         Renders a deploy script for the specified
                                virt-who configuration
    info                          Show a virt-who configuration
    list                          List of virt-who configurations
    update                        Update a virt-who configuration
"""

from robottelo.cli.base import Base


class VirtWhoConfig(Base):
    """Manipulates virt-who configuration."""

    command_base = 'virt-who-config'

    @classmethod
    def fetch(cls, options=None, output_format=None):
        """Renders a deploy script for the specified virt-who configuration"""
        cls.command_sub = 'fetch'
        return cls.execute(cls._construct_command(options), output_format=output_format)

    @classmethod
    def deploy(cls, options=None):
        """runs hammer virt-who-config deploy --id <x> which runs the script on
        the satellite server

        :param options: `id` required
        :return: Results of the command
        """
        cls.command_sub = 'deploy'
        return cls.execute(cls._construct_command(options))
