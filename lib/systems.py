#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from common import *
from locators import *

from robot.api import logger
from robot.utils import asserts

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


class systems(object):
    """
    Perform tasks on systems, such as adding, removing subscriptions.
    """
    __version__ = '0.1'


    def __init__(self):
        self.base = Base()

    def go_to_systems_tab(self):
        """
        Takes user to the Systems tab.
        """

        return select_tab(self.base.driver, SYSTEMS_TAB)
