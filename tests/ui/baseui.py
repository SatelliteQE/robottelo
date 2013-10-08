#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging
import logging.config
import os
import unittest

from splinter import Browser

class BaseUI(unittest.TestCase):

    def setUp(self):
        self.host = os.getenv('KATELLO_HOST')
        self.port = os.getenv('KATELLO_PORT', '443')
        self.project = os.getenv('PROJECT', 'katello')
        self.driver_name = os.getenv('DRIVER_NAME', 'firefox')

        self.verbosity = int(os.getenv('VERBOSITY', 2))

        logging.config.fileConfig("logging.conf")

        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)

        self.browser = Browser(driver_name=self.driver_name)
        self.browser.visit("%s/%s" % (self.host, self.project))

    def tearDown(self):
        self.browser.quit()
        self.browser = None

