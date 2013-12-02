#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base


class Architecture(Base):

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "architecture"
