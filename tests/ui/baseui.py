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
import sauceclient

from robottelo.lib.ui.login import Login
from robottelo.lib.ui.navigator import Navigator
from robottelo.lib.ui.user import User
from selenium import webdriver

SCREENSHOTS_DIR = os.path.join(
    os.path.abspath(os.path.curdir), 'screenshots')



class BaseUI(unittest.TestCase):

    def setUp(self):
        self.host = os.getenv('KATELLO_HOST')
        self.port = os.getenv('KATELLO_PORT', '443')
        self.project = os.getenv('PROJECT', 'katello')
        self.driver_name = os.getenv('DRIVER_NAME', 'firefox')
        self.sauce_user = os.getenv('SAUCE_USER','')
        self.sauce_key = os.getenv('SAUCE_KEY')
        self.sauce_os = os.getenv('SAUCE_OS')
        self.sauce_version = os.getenv('SAUCE_VERSION')
        self.verbosity = int(os.getenv('VERBOSITY', 2))

        logging.config.fileConfig("logging.conf")

        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)
        if len(self.sauce_user) == 0:
            if self.driver_name.lower() == 'firefox':
                self.browser = webdriver.Firefox()
            elif self.driver_name.lower() == 'chrome':
                self.browser = webdriver.Chrome()
            elif self.driver_name.lower() == 'ie':
                self.browser = webdriver.Ie()
            else:
                self.browser = webdriver.Remote()
        else:
            desired_capabilities = getattr(webdriver.DesiredCapabilities, self.driver_name.upper())
            desired_capabilities['version'] = self.sauce_version
            desired_capabilities['platform'] = self.sauce_os
            self.browser = webdriver.Remote(
                desired_capabilities=desired_capabilities,
                command_executor="http://"+self.sauce_user+":"+self.sauce_key+"@ondemand.saucelabs.com:80/wd/hub")
            self.browser.implicitly_wait(3)

        self.browser.maximize_window()
        self.browser.get("%s/%s" % (self.host, self.project))

        # Library methods
        self.login = Login(self.browser)
        self.navigator = Navigator(self.browser)
        self.user = User(self.browser)

    # Borrowed from the following article:
    #  http://engineeringquality.blogspot.com/2012/12/python-selenium-capturing-screenshot-on.html
    def take_screenshot(self, file_name="error.png"):
            """
            @param file_name: Name to label this screenshot.
            @type file_name: str
            """

            if not os.path.exists(SCREENSHOTS_DIR):
                try:
                    os.mkdir(SCREENSHOTS_DIR)
                    file_name = os.path.join(SCREENSHOTS_DIR, file_name)
                except Exception, e:
                    self.logger.debug(
                        "Could not create screenshots directory: %s" % str(e))
                    pass

            if isinstance(
                    self.browser,
                    selenium.webdriver.remote.webdriver.WebDriver):
                # Get Screenshot over the wire as base64
                base64_data = self.browser.get_screenshot_as_base64()
                screenshot_data = base64.decodestring(base64_data)
                screenshot_file = open(file_name, "w")
                screenshot_file.write(screenshot_data)
                screenshot_file.close()
            else:
                self.browser.save_screenshot(file_name)

    def run(self, result=None):
        super(BaseUI, self).run(result)
        # create a sauceclient object to report pass/fail results
        sc = sauceclient.SauceClient(
            self.sauce_user,
            self.sauce_key)

        if result.failures or result.errors:
            fname = str(self).replace(
                "(", "").replace(")", "").replace(" ", "_")
            fmt = '%y-%m-%d_%H.%M.%S'
            fdate = datetime.datetime.now().strftime(fmt)
            filename = "%s_%s.png" % (fdate, fname)
            self.take_screenshot(filename)
            if "remote" in str(type(self.browser)):
                print self.browser
                sc.jobs.update_job(self.browser.session_id,name=str(self),passed=False)
        else:
            if "remote" in str(type(self.browser)):
                sc.jobs.update_job(self.browser.session_id,name=str(self),passed=True)

        self.browser.quit()
        self.browser = None

        return result
