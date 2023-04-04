"""
Usage::

    hammer alternate-content-source [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND      Subcommand
    [ARG] ...       Subcommand arguments

Subcommands::

    create          Create an alternate content source to download content from during repository
                    syncing. Note: alternate content sources are global and affect ALL sync actions
                    on their capsules regardless of organization.
    delete          Destroy an alternate content source.
    info            Show an alternate content source.
    list            List alternate content sources.
    refresh         Refresh an alternate content source. Refreshing, like repository syncing, is
                    required before using an alternate content source.
    update          Update an alternate content source.

"""
from robottelo.cli.base import Base


class ACS(Base):
    """
    Manipulates Alternate Content Sources
    """

    command_base = 'alternate-content-source'

    @classmethod
    def refresh(cls, options=None):
        """Refresh the ACS"""
        cls.command_sub = 'refresh'
        return cls.execute(cls._construct_command(options))
