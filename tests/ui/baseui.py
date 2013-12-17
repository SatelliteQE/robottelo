#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import datetime
import logging
import os
import unittest
import sauceclient

from robottelo.common import conf
from robottelo.ui.architecture import Architecture
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.login import Login
from robottelo.ui.medium import Medium
from robottelo.ui.navigator import Navigator
from robottelo.ui.operatingsys import OperatingSys
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.product import Product
from robottelo.ui.hosts import Hosts
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.subnet import Subnet
from robottelo.ui.template import Template
from robottelo.ui.user import User
from selenium import webdriver

SCREENSHOTS_DIR = os.path.join(
    os.path.abspath(os.path.curdir), 'screenshots')

SAUCE_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"


class BaseUI(unittest.TestCase):

    def setUp(self):
        self.host = conf.properties['main.server.hostname']
        self.katello_user = conf.properties['foreman.admin.username']
        self.katello_passwd = conf.properties['foreman.admin.password']
        self.driver_name = conf.properties['saucelabs.driver']
        self.sauce_user = conf.properties['saucelabs.username']
        self.sauce_key = conf.properties['saucelabs.key']
        self.sauce_os = conf.properties['saucelabs.os']
        self.sauce_tunnel = conf.properties['saucelabs.tunnel']
        self.sauce_version = conf.properties['saucelabs.browser.version']
        self.locale = conf.properties['main.locale']
        self.verbosity = int(conf.properties['nosetests.verbosity'])
        self.remote = int(conf.properties['main.remote'])

        self.logger = logging.getLogger("robottelo")

        if not self.remote:
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
                command_executor=SAUCE_URL % (self.sauce_user, self.sauce_key))
            self.browser.implicitly_wait(3)

        self.browser.maximize_window()
        self.browser.get("https://" + self.host)

        # Library methods
        self.login = Login(self.browser)
        self.navigator = Navigator(self.browser)
        self.product = Product(self.browser)
        self.user = User(self.browser)
        self.operatingsys = OperatingSys(self.browser)
        self.environment = Environment(self.browser)
        self.architecture = Architecture(self.browser)
        self.medium = Medium(self.browser)
        self.hosts = Hosts(self.browser)
        self.hostgroup = Hostgroup(self.browser)
        self.domain = Domain(self.browser)
        self.subnet = Subnet(self.browser)
        self.template = Template(self.browser)
        self.partitiontable = PartitionTable(self.browser)

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
        if not "remote" in str(type(self.browser)):
            self.browser.save_screenshot(file_name)

    def run(self, result=None):
        super(BaseUI, self).run(result)

        try:
            if result.skipped:
                try:
                    self.browser.quit()
                except Exception:
                    pass

                return result
        except AttributeError:
            pass

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
