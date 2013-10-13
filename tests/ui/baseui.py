#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import base64
import datetime
import logging
import logging.config
import os
import selenium
import unittest

from robottelo.lib.ui.login import Login
from robottelo.lib.ui.navigator import Navigator
from robottelo.lib.ui.user import User

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
        self.browser.driver.maximize_window()
        self.browser.visit("%s/%s" % (self.host, self.project))

        # Library methods
        self.login = Login(self.browser)
        self.navigator = Navigator(self.browser)
        self.user = User(self.browser)

    # Borrowed from the following article:
    #  http://engineeringquality.blogspot.com/2012/12/python-selenium-capturing-screenshot-on.html
    def take_screenshot(self, webdriver, file_name="error.png"):
            """
            @param webdriver: WebDriver.
            @type webdriver: WebDriver
            @param file_name: Name to label this screenshot.
            @type file_name: str
            """
            if isinstance(webdriver, selenium.webdriver.remote.webdriver.WebDriver):
                # Get Screenshot over the wire as base64
                base64_data = webdriver.get_screenshot_as_base64()
                screenshot_data = base64.decodestring(base64_data)
                screenshot_file = open(file_name, "w")
                screenshot_file.write(screenshot_data)
                screenshot_file.close()
            else:
                webdriver.save_screenshot(filename)

    def run(self, result=None):
        super(BaseUI, self).run(result)

        if result.failures or result.errors:
            fname = str(self).replace("(", "").replace(")", "").replace(" ", "_")
            fmt='%y-%m-%d_%H.%M.%S'
            fdate = datetime.datetime.now().strftime(fmt)
            filename = "%s_%s.png" % (fdate, fname)
            self.take_screenshot(self.browser.driver, filename)

        self.browser.quit()
        self.browser = None

        return result

