#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import datetime
import logging
import logging.config
import os
import selenium
import unittest
import sauceclient

from lib.ui.login import Login
from lib.ui.navigator import Navigator
from lib.ui.product import Product
from lib.ui.user import User
from selenium import webdriver

SCREENSHOTS_DIR = os.path.join(
    os.path.abspath(os.path.curdir), 'screenshots')

SAUCE_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"


class BaseUI(unittest.TestCase):

    def setUp(self):
        self.host = os.getenv('KATELLO_HOST')
        self.port = os.getenv('KATELLO_PORT', '443')
        self.project = os.getenv('PROJECT', 'katello')
        self.katello_user = os.getenv('KATELLO_USER')
        self.katello_passwd = os.getenv('KATELLO_PASSWD')
        self.driver_name = os.getenv('DRIVER_NAME', 'firefox')
        self.sauce_user = os.getenv('SAUCE_USER')
        self.sauce_key = os.getenv('SAUCE_KEY')
        self.sauce_os = os.getenv('SAUCE_OS')
        self.sauce_tunnel = os.getenv('SAUCE_TUNNEL')
        self.sauce_version = os.getenv('SAUCE_VERSION')
        self.locale = os.getenv('LOCALE', 'en_US')
        self.verbosity = int(os.getenv('VERBOSITY'))

        logging.config.fileConfig("logging.conf")

        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)

        if self.sauce_user is None:
            if self.driver_name.lower() == 'firefox':
                self.browser = webdriver.Firefox()
            elif self.driver_name.lower() == 'chrome':
                self.browser = webdriver.Chrome()
            elif self.driver_name.lower() == 'ie':
                self.browser = webdriver.Ie()
            else:
                self.browser = webdriver.Remote()
        else:
            desired_capabilities = getattr(
                webdriver.DesiredCapabilities, self.driver_name.upper())
            desired_capabilities['version'] = self.sauce_version
            desired_capabilities['platform'] = self.sauce_os

            if self.sauce_tunnel is not None:
                desired_capabilities['parent-tunnel'] = self.sauce_tunnel
            self.browser = webdriver.Remote(
                desired_capabilities=desired_capabilities,
                command_executor = SAUCE_URL % (self.sauce_user, self.sauce_key))
            self.browser.implicitly_wait(3)

        self.browser.maximize_window()
        self.browser.get(self.host)

        # Library methods
        self.login = Login(self.browser)
        self.navigator = Navigator(self.browser)
        self.product = Product(self.browser)
        self.user = User(self.browser)

    def take_screenshot(self, file_name="error.png"):
            """
            Takes screenshot of the UI if running locally.

            @param file_name: Name to label this screenshot.
            @type file_name: str
            """

            # Create screenshot directory if it doesn't exist
            if not os.path.exists(SCREENSHOTS_DIR):
                try:
                    os.mkdir(SCREENSHOTS_DIR)
                except Exception, e:
                    self.logger.debug(
                        "Could not create screenshots directory: %s" % str(e))
                    pass
            else:
                file_name = os.path.join(SCREENSHOTS_DIR, file_name)

            if not isinstance(
                    self.browser,
                    selenium.webdriver.remote.webdriver.WebDriver):
                self.browser.save_screenshot(file_name)

    def run(self, result=None):
        super(BaseUI, self).run(result)

        if result.skipped:
            try:
                self.browser.quit()
            except Exception, e:
                pass

            return result

        # create a sauceclient object to report pass/fail results
        if "remote" in str(type(self.browser)):
            sc = sauceclient.SauceClient(
                self.sauce_user,
                self.sauce_key)

        if result.failures or result.errors:

            # Take screenshot
            fname = str(self).replace(
                "(", "").replace(")", "").replace(" ", "_")
            fmt = '%y-%m-%d_%H.%M.%S'
            fdate = datetime.datetime.now().strftime(fmt)
            filename = "%s_%s.png" % (fdate, fname)
            self.take_screenshot(filename)

            # Mark test as passed remotely
            if "remote" in str(type(self.browser)):
                sc.jobs.update_job(
                    self.browser.session_id, name=str(self), passed=False)
        else:
            if "remote" in str(type(self.browser)):
                sc.jobs.update_job(
                    self.browser.session_id, name=str(self), passed=True)

        self.browser.quit()
        self.browser = None

        return result
