# -*- encoding: utf-8 -*-
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
