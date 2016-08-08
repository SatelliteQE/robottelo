# -*- encoding: utf-8 -*-
"""Implements different locators for UI"""

from selenium.webdriver.common.by import By  # noqa
from .model import Locator, LocatorDict  # noqa
from .menu import menu_locators  # noqa
from .tab import tab_locators  # noqa
from .common import common_locators  # noqa
from .base import locators  # noqa
