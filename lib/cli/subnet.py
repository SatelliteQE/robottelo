# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base


class Subnet(Base):

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "subnet"
