# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all cli tests
"""

import logging
import unittest


class BaseAPI(unittest.TestCase):
    """
    Base class for all cli tests
    """

    def setUp(self):
        self.logger = logging.getLogger("robottelo")
