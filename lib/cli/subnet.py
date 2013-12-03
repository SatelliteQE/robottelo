# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base
from lib.common.helpers import generate_ip3, generate_name


class Subnet(Base):

    OUT_SUBNET_DELETED = "Subnet deleted"

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "subnet"

    def create_minimal(self, name=generate_name(8, 8), network=generate_ip3()):
        options = {}
        options['name'] = name
        options['network'] = network
        options['mask'] = '255.255.255.0'
        return self.create(options)
