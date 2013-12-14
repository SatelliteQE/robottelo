#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer global_parameter [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set                           Set a global parameter.
    list                          List all common parameters.
    delete                        Delete a common_parameter
"""
from robottelo.cli.base import Base


class GlobalParameter(Base):

    def __init__(self):
        self.command_base = "global_parameter"

    def set(self, options=None):
        """ Set global parameter """
        self.command_sub = "set"
        return self.execute(self._construct_command(options))
