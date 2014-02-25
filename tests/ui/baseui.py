# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all UI tests
"""

import logging
import unittest

from robottelo.common import conf
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.contentenv import ContentEnvironment
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hosts import Hosts
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.login import Login
from robottelo.ui.medium import Medium
from robottelo.ui.navigator import Navigator
from robottelo.ui.operatingsys import OperatingSys
from robottelo.ui.org import Org
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.products import Products
from robottelo.ui.repository import Repos
from robottelo.ui.role import Role
from robottelo.ui.subnet import Subnet
from robottelo.ui.sync import Sync
from robottelo.ui.template import Template
from robottelo.ui.user import User
from robottelo.ui.usergroup import UserGroup
from selenium import webdriver
from selenium_factory.SeleniumFactory import SeleniumFactory

SAUCE_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"


class BaseUI(unittest.TestCase):
    """
    Base class for all UI tests.
    """

    @classmethod
    def setUpClass(cls):
        """
        Make sure that we only read configuration values once.
        """

        cls.host = conf.properties['main.server.hostname']
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.driver_name = conf.properties['saucelabs.driver']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['nosetests.verbosity'])
        cls.remote = int(conf.properties['main.remote'])

        cls.logger = logging.getLogger("robottelo")

    def setUp(self):
        """
        We do want a new browser instance for every test.
        """

        if not self.remote:
            if self.driver_name.lower() == 'firefox':
                self.browser = webdriver.Firefox()
            elif self.driver_name.lower() == 'chrome':
                self.browser = webdriver.Chrome()
            elif self.driver_name.lower() == 'ie':
                self.browser = webdriver.Ie()
            elif self.driver_name.lower() == 'phantomjs':
                service_args = ['--ignore-ssl-errors=true']
                self.browser = webdriver.PhantomJS(
                    service_args=service_args
                    )
            else:
                self.browser = webdriver.Remote()
        else:
            self.browser = SeleniumFactory().createWebDriver(
                job_name=self.id(), show_session_id=True)

        self.browser.maximize_window()
        self.browser.get("https://" + self.host)

        # Library methods
        self.activationkey = ActivationKey(self.browser)
        self.architecture = Architecture(self.browser)
        self.contentenv = ContentEnvironment(self.browser)
        self.compute_resource = ComputeResource(self.browser)
        self.domain = Domain(self.browser)
        self.environment = Environment(self.browser)
        self.gpgkey = GPGKey(self.browser)
        self.hostgroup = Hostgroup(self.browser)
        self.hosts = Hosts(self.browser)
        self.login = Login(self.browser)
        self.medium = Medium(self.browser)
        self.navigator = Navigator(self.browser)
        self.user = User(self.browser)
        self.operatingsys = OperatingSys(self.browser)
        self.org = Org(self.browser)
        self.partitiontable = PartitionTable(self.browser)
        self.products = Products(self.browser)
        self.repository = Repos(self.browser)
        self.role = Role(self.browser)
        self.subnet = Subnet(self.browser)
        self.sync = Sync(self.browser)
        self.template = Template(self.browser)
        self.user = User(self.browser)
        self.usergroup = UserGroup(self.browser)

    def tearDown(self):
        """
        Make sure to close the browser after each test.
        """

        self.browser.quit()
        self.browser = None
