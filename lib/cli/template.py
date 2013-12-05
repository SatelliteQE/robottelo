#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from lib.common.helpers import csv_to_dictionary


class Template(Base):

    def __init__(self):
        self.command_base = "template"

    def kinds(self):
        """
        Returns list of types of templates.
        """

        cmd = "template kinds"

        stdout, stderr = self.execute(cmd)

        kinds = []
        if stdout:
            kinds = csv_to_dictionary(stdout)

        return kinds
