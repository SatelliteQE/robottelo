#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config
import unittest
from lib.cli.architecture import Architecture
from lib.cli.domain import Domain
from lib.cli.host import Host
from lib.cli.hostgroup import Hostgroup
from lib.cli.medium import Medium
from lib.cli.operatingsys import OperatingSys
from lib.cli.partitiontable import PartitionTable
from lib.cli.subnet import Subnet
from lib.cli.template import Template
from lib.cli.user import User
from lib.common import conf
from lib.cli.base import Base


class BaseCLI(unittest.TestCase):

    __initialized = False

    def _init_once(self):
        """
        A way to define stuff to be initialized in your test class.
        Override /me if needed.
        """
        pass

    def __init_once_me(self):
        """
        Local initialization - needed to be done once.
        """
        self.__class__.hostname = conf.properties['main.server.hostname']
        self.__class__.katello_user = \
            conf.properties['foreman.admin.username']
        self.__class__.katello_passwd = \
            conf.properties['foreman.admin.password']
        self.__class__.key_filename = \
            conf.properties['main.server.ssh.key_private']
        self.__class__.root = conf.properties['main.server.ssh.username']
        self.__class__.locale = conf.properties['main.locale']
        self.__class__.verbosity = int(conf.properties['nosetests.verbosity'])

        logging.config.fileConfig("%s/logging.conf" % conf.get_root_path())
        # Hide base logger from paramiko
        logging.getLogger("paramiko").setLevel(logging.ERROR)

        self.__class__.logger = logging.getLogger("robottelo")
        self.__class__.logger.setLevel(self.verbosity * 10)

        # Library methods
        self.__class__.arch = Architecture()
        self.__class__.domain = Domain()
        self.__class__.host = Host()
        self.__class__.hostgroup = Hostgroup()
        self.__class__.medium = Medium()
        self.__class__.os = OperatingSys()
        self.__class__.ptable = PartitionTable()
        self.__class__.subnet = Subnet()
        self.__class__.template = Template()
        self.__class__.user = User()

    def setUp(self):
        if not self.__initialized:
            self.__init_once_me()
            self._init_once()
            self.__class__.__initialized = True

    def upload_file(self, local_file, remote_file=None):
        """
        Uploads a remote file to a server.
        """

        if not remote_file:
            remote_file = local_file

        sftp = Base.get_connection().open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()
