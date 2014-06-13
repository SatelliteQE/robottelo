# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base classes for all cli tests
"""

import logging
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from robottelo.cli.metatest import MetaCLITest
from robottelo.common import conf


class BaseCLI(unittest.TestCase):
    """
    Base class for all cli tests
    """

    @classmethod
    def setUpClass(cls):
        """
        Make sure that we only read configuration values once.
        """

        cls.hostname = conf.properties['main.server.hostname']
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.key_filename = conf.properties['main.server.ssh.key_private']
        cls.root = conf.properties['main.server.ssh.username']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['nosetests.verbosity'])

        # Hide base logger from paramiko
        logging.getLogger("paramiko").setLevel(logging.ERROR)
        cls.logger = logging.getLogger("robottelo")

    def setUp(self):
        """
        Log test class and method name before each test.
        """
        self.logger.debug("Running test %s/%s", type(self).__name__,
                          self._testMethodName)


class MetaCLI(BaseCLI):

    """
    All Test modules should inherit from MetaCLI in order to obtain default
    positive/negative CRUD tests.
    """
    __metaclass__ = MetaCLITest
