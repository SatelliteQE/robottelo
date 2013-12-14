#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.cli.base import Base


class Architecture(Base):

    def __init__(self):
        self.command_base = "architecture"
