# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config
import unittest

from lib.common import conf


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

    def setUp(self):
        if not self.__initialized:
            self.__init_once_me()
            self.__class__.__initialized = True
            self._init_once()
