#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.cli.base import Base


class Proxy(Base):

    def __init__(self):
        self.command_base = "proxy"

    def import_classes(self, options=None):
        """
        Import puppet classes from puppet proxy.
        """

        self.command_sub = "import_classes"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True
