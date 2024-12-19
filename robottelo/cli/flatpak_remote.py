"""
Usage::

    hammer flatpak-remote [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND      Subcommand
    [ARG] ...       Subcommand arguments

Subcommands::

    create                        Create a flatpak remote
    delete                        Delete a flatpak remote
    info                          Show a flatpak remote
    list                          List flatpak remotes
    remote-repository             View and manage flatpak remote repositories
    scan                          Scan a flatpak remote
    update                        Update a flatpak remote

"""

from robottelo.cli.base import Base


class FlatpakRemote(Base):
    """
    Manipulates Flatpak remotes and repositories
    """

    command_base = 'flatpak-remote'

    @classmethod
    def scan(cls, options=None, output_format=None):
        """Scan a flatpak remote"""
        cls.command_sub = 'scan'
        return cls.execute(cls._construct_command(options), output_format=output_format)

    @classmethod
    def repository_info(cls, options=None, output_format='csv'):
        """Show a flatpak remote repository"""
        cls.command_sub = 'remote-repository info'
        return cls.execute(cls._construct_command(options), output_format=output_format)

    @classmethod
    def repository_list(cls, options=None, output_format='csv'):
        """List flatpak remote repositories"""
        cls.command_sub = 'remote-repository list'
        return cls.execute(cls._construct_command(options), output_format=output_format)

    @classmethod
    def repository_mirror(cls, options=None, output_format=None):
        """Mirror a flatpak remote repository"""
        cls.command_sub = 'remote-repository mirror'
        return cls.execute(cls._construct_command(options), output_format=output_format)
