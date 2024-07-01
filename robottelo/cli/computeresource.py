"""
Usage::

    hammer compute-resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
"""

from robottelo.cli.base import Base


class ComputeResource(Base):
    """
    Manipulates Foreman's compute resources.
    """

    command_base = 'compute-resource'

    @classmethod
    def image_create(cls, options):
        """Create an image"""
        cls.command_sub = 'image create'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def image_info(cls, options):
        """Show an image"""
        cls.command_sub = 'image info'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def image_available(cls, options):
        """Show images available for addition"""
        cls.command_sub = 'image available'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def image_delete(cls, options):
        """delete an image"""
        cls.command_sub = 'image delete'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def image_list(cls, options):
        """Show the list of images"""
        cls.command_sub = 'image list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def image_update(cls, options):
        """update an image"""
        cls.command_sub = 'image update'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def networks(cls, options):
        """List available networks for a compute resource"""
        cls.command_sub = 'networks'
        return cls.execute(cls._construct_command(options), output_format='csv')
