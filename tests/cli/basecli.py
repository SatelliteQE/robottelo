#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging
import logging.config
import os
import sys
import unittest

from robottelo.lib.cli.user import User

try:
    import paramiko
except Exception, e:
    print "Please install paramiko."
    sys.exit(-1)

class BaseCLI(unittest.TestCase):

    def setUp(self):
        self.host = os.getenv('KATELLO_HOST')
        self.key_filename = os.getenv('SSH_KEY')
        self.root = os.getenv('ROOT')
        self.verbosity = int(os.getenv('VERBOSITY', 2))

        logging.config.fileConfig("logging.conf")
        # Hide base logger from paramiko
        logging.getLogger("paramiko").setLevel(logging.ERROR)

        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)

        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #key = paramiko.RSAKey.from_private_key_file(self.key_filename)
        self.conn.connect(self.host, username=self.root, key_filename=self.key_filename)

        # Library methods
        self.user = User(self.conn)
