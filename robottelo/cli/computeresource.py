# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer compute_resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a compute resource.
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images
"""
from robottelo.cli.base import Base


class ComputeResource(Base):
    """
    Manipulates Foreman's compute resources.
    """

    command_base = "compute_resource"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
