#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config
import sys
import unittest
from lib.cli.architecture import Architecture
from lib.cli.hostgroup import Hostgroup
from lib.cli.medium import Medium
from lib.cli.operatingsys import OperatingSys
from lib.cli.partitiontable import PartitionTable
from lib.cli.subnet import Subnet
from lib.cli.template import Template
from lib.cli.user import User
from lib.common import conf

try:
    import paramiko
except Exception, e:
    print "Please install paramiko."
    sys.exit(-1)


class BaseCLI(unittest.TestCase):

    def setUp(self):
        self.host = conf.properties['main.server.hostname']
        self.katello_user = conf.properties['foreman.admin.username']
        self.katello_passwd = conf.properties['foreman.admin.password']
        self.key_filename = conf.properties['main.server.ssh.key_private']
        self.root = conf.properties['main.server.ssh.username']
        self.locale = conf.properties['main.locale']
        self.verbosity = int(conf.properties['nosetests.verbosity'])

        logging.config.fileConfig("%s/logging.conf" % conf.get_root_path())
        # Hide base logger from paramiko
        logging.getLogger("paramiko").setLevel(logging.ERROR)

        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)

        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #key = paramiko.RSAKey.from_private_key_file(self.key_filename)
        self.conn.connect(self.host, username=self.root,
                          key_filename=self.key_filename)

        # Library methods
        self.arch = Architecture(self.conn)
        self.hostgroup = Hostgroup(self.conn)
        self.medium = Medium(self.conn)
        self.os = OperatingSys(self.conn)
        self.ptable = PartitionTable(self.conn)
        self.subnet = Subnet(self.conn)
        self.template = Template(self.conn)
        self.user = User(self.conn)

    def upload_file(self, local_file, remote_file=None):
        """
        Uploads a remote file to a server.
        """

        if not remote_file:
            remote_file = local_file

        sftp = self.conn.open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()
