"""
Usage::
    hammer template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::
    SUBCOMMAND                    Subcommand
    [ARG] ...                     Subcommand arguments

Subcommands::
    add-operatingsystem           Associate an operating system
    build-pxe-default             Update the default PXE menu on all configured TFTP servers
    clone                         Clone a provision template
    combination                   Manage template combinations
    create                        Create a provisioning template
    delete                        Delete a provisioning template
    dump                          View provisioning template content
    info                          Show provisioning template details
    kinds                         List available provisioning template kinds
    list                          List provisioning templates
    remove-operatingsystem        Disassociate an operating system
    update                        Update a provisioning template
"""

from robottelo.cli.base import Base


class Template(Base):
    """Manipulates Foreman's configuration templates."""

    command_base = 'template'

    @classmethod
    def kinds(cls, options=None):
        """Returns list of types of templates."""
        cls.command_sub = 'kinds'

        result = cls.execute(cls._construct_command(options), output_format='csv')

        kinds = []
        if result:
            kinds = result

        return kinds

    @classmethod
    def add_operatingsystem(cls, options=None):
        """Adds operating system, requires "id" and "operatingsystem-id"."""
        cls.command_sub = 'add-operatingsystem'

        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_operatingsystem(cls, options=None):
        """Remove operating system, requires "id" and "operatingsystem-id"."""
        cls.command_sub = 'remove-operatingsystem'

        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def clone(cls, options=None):
        """Clone provided provisioning template"""
        cls.command_sub = 'clone'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def build_pxe_default(cls, options=None):
        """Build PXE default template"""
        cls.command_sub = 'build-pxe-default'
        return cls.execute(cls._construct_command(options), output_format='csv')
