"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
to help writting API, CLI and UI tests.

"""
import logging
import os
import signal
import sys
try:
    import unittest
except ImportError:
    import unittest2 as unittest

from automation_tools import product_install
from datetime import datetime
from fabric.api import execute, settings
from robottelo.cli.metatest import MetaCLITest
from robottelo.common.helpers import get_server_url
from robottelo.common import conf
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.configgroups import ConfigGroups
from robottelo.ui.contentenv import ContentEnvironment
from robottelo.ui.contentviews import ContentViews
from robottelo.ui.contentsearch import ContentSearch
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hardwaremodel import HardwareModel
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.hosts import Hosts
from robottelo.ui.location import Location
from robottelo.ui.login import Login
from robottelo.ui.medium import Medium
from robottelo.ui.navigator import Navigator
from robottelo.ui.operatingsys import OperatingSys
from robottelo.ui.org import Org
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.products import Products
from robottelo.ui.puppetclasses import PuppetClasses
from robottelo.ui.repository import Repos
from robottelo.ui.role import Role
from robottelo.ui.settings import Settings
from robottelo.ui.subnet import Subnet
from robottelo.ui.subscription import Subscriptions
from robottelo.ui.sync import Sync
from robottelo.ui.syncplan import Syncplan
from robottelo.ui.systemgroup import SystemGroup
from robottelo.ui.template import Template
from robottelo.ui.trend import Trend
from robottelo.ui.usergroup import UserGroup
from robottelo.ui.user import User
from robottelo.vm import VirtualMachine
from selenium_factory.SeleniumFactory import SeleniumFactory
from selenium import webdriver


SAUCE_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"


class TestCase(unittest.TestCase):
    """Robottelo test case"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(TestCase, cls).setUpClass()
        cls.logger = logging.getLogger('robottelo')
        # NOTE: longMessage defaults to True in Python 3.1 and above
        cls.longMessage = True


class APITestCase(TestCase):
    """Test case for API tests."""
    _multiprocess_can_split_ = True


class CLITestCase(TestCase):
    """Test case for CLI tests."""
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls):  # noqa
        """Make sure that we only read configuration values once."""
        super(CLITestCase, cls).setUpClass()
        cls.hostname = conf.properties['main.server.hostname']
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.key_filename = conf.properties['main.server.ssh.key_private']
        cls.root = conf.properties['main.server.ssh.username']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['main.verbosity'])

    def setUp(self):  # noqa
        """Log test class and method name before each test."""
        self.logger.debug(
            "Running test %s/%s", type(self).__name__, self._testMethodName)


class MetaCLITestCase(CLITestCase):
    """All Test modules should inherit from MetaCLI in order to obtain default
    positive/negative CRUD tests.

    """
    __metaclass__ = MetaCLITest


class UITestCase(TestCase):
    """Test case for UI tests."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Make sure that we only read configuration values once."""
        super(UITestCase, cls).setUpClass()
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.driver_name = conf.properties['saucelabs.driver']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['main.verbosity'])
        cls.remote = int(conf.properties['main.remote'])
        cls.server_name = conf.properties.get('main.server.hostname')
        cls.screenshots_dir = conf.properties.get('main.screenshots.base_path')

        if int(conf.properties.get('main.virtual_display', '0')):
            # Import from optional requirements
            from pyvirtualdisplay import Display
            from easyprocess import EasyProcess, EasyProcessError
            cls.display = Display(size=(1920, 1080))
            cls.display.start()
            cls.logger.debug(
                'Virtual display started (pid=%d, display="%s")',
                cls.display.pid,
                cls.display.display
            )

            window_manager_cmd = conf.properties.get(
                'main.window_manager_command', '')

            try:
                cls.window_manager = EasyProcess(window_manager_cmd)
                cls.window_manager.start()
                cls.logger.debug(
                    'Window manager started (pid=%d, cmd="%s")',
                    cls.window_manager.pid,
                    cls.window_manager.cmd_as_string
                )
            except EasyProcessError as err:
                cls.window_manager = None
                cls.logger.warning(
                    'Window manager could not be started. '
                    'Command: "%s". Error: %s',
                    window_manager_cmd,
                    err
                )
        else:
            cls.display = None

    def setUp(self):  # noqa
        """We do want a new browser instance for every test."""
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
        self.browser.get(get_server_url())

        # Library methods
        self.activationkey = ActivationKey(self.browser)
        self.architecture = Architecture(self.browser)
        self.compute_resource = ComputeResource(self.browser)
        self.configgroups = ConfigGroups(self.browser)
        self.contentenv = ContentEnvironment(self.browser)
        self.content_views = ContentViews(self.browser)
        self.content_search = ContentSearch(self.browser)
        self.domain = Domain(self.browser)
        self.environment = Environment(self.browser)
        self.gpgkey = GPGKey(self.browser)
        self.hardwaremodel = HardwareModel(self.browser)
        self.hostgroup = Hostgroup(self.browser)
        self.hosts = Hosts(self.browser)
        self.location = Location(self.browser)
        self.login = Login(self.browser)
        self.medium = Medium(self.browser)
        self.navigator = Navigator(self.browser)
        self.user = User(self.browser)
        self.operatingsys = OperatingSys(self.browser)
        self.org = Org(self.browser)
        self.partitiontable = PartitionTable(self.browser)
        self.puppetclasses = PuppetClasses(self.browser)
        self.products = Products(self.browser)
        self.repository = Repos(self.browser)
        self.role = Role(self.browser)
        self.settings = Settings(self.browser)
        self.subnet = Subnet(self.browser)
        self.subscriptions = Subscriptions(self.browser)
        self.sync = Sync(self.browser)
        self.syncplan = Syncplan(self.browser)
        self.systemgroup = SystemGroup(self.browser)
        self.template = Template(self.browser)
        self.trend = Trend(self.browser)
        self.user = User(self.browser)
        self.usergroup = UserGroup(self.browser)

    def take_screenshot(self, testmethodname):
        """Takes screenshot of the UI and saves it to the disk by creating
        a directory same as that of the test method name."""
        # testmethodname varies so trying to handle various scenarios.
        # pop depending on ddt, normal test or ddt's 1st job.
        # For ddt tests with maps.
        if "___" in testmethodname:
            parts = testmethodname.split("___")
        # For ddt tests with utf8, html, etc.
        elif "__" in testmethodname:
            parts = testmethodname.split("__")
        # For ddt test with alpha, numeric, etc.
        else:
            testmethodname = testmethodname.split('_')
            # Do Nothing for Non DDT Tests.
            if len(testmethodname[-2]) == 1:
                for _ in range(2):
                    testmethodname.pop()
        if "___" in testmethodname or "__" in testmethodname:
            testmethodname = parts[0]
            testmethodname = testmethodname.split('_')
            testmethodname.pop()
        testmethodname = "_".join(testmethodname)
        # Creates dir_structure depending upon the testmethodname.
        directory = testmethodname
        dir_structure = os.path.join(
            self.screenshots_dir,
            datetime.now().strftime('%Y-%m-%d'),
            directory,
        )
        if not os.path.exists(dir_structure):
            os.makedirs(dir_structure)
        filename = 'screenshot-{0}.png'.format(
            datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
        )
        self.browser.save_screenshot(os.path.join(dir_structure, filename))

    def tearDown(self):  # noqa
        """Make sure to close the browser after each test."""
        if sys.exc_info()[0] is not None:
            self.take_screenshot(self._testMethodName)
        self.browser.quit()
        self.browser = None

    @classmethod
    def tearDownClass(cls):  # noqa
        if cls.display is not None:
            if (cls.window_manager is not None and
                    cls.window_manager.is_started):
                cls.logger.debug(
                    'Killing window manager (pid=%d, cmd="%s")',
                    cls.window_manager.pid,
                    cls.window_manager.cmd_as_string
                )
                os.kill(cls.window_manager.pid, signal.SIGKILL)
                _, return_code = os.waitpid(cls.window_manager.pid, 0)
                cls.logger.debug(
                    'Window manager killed (pid=%d, cmd="%s", rcode=%d)',
                    cls.window_manager.pid,
                    cls.window_manager.cmd_as_string,
                    return_code
                )
            cls.logger.debug(
                'Stopping virtual display (pid=%d, display="%s"',
                cls.display.pid,
                cls.display.display
            )
            cls.display.stop()
            cls.logger.debug(
                'Virtual display stopped (pid=%d, display="%s"',
                cls.display.pid,
                cls.display.display
            )


class InstallerTestCase(TestCase):
    vm_cpu = 2
    vm_ram = 6144
    vm_os = 'rhel71'

    @classmethod
    def setUpClass(cls):  # noqa
        super(InstallerTestCase, cls).setUpClass()
        cls.vm = VirtualMachine(cls.vm_cpu, cls.vm_ram, cls.vm_os)
        cls.vm.create()
        key_filename = conf.properties.get('main.server.ssh.key_private')
        with settings(key_filename=key_filename, user='root', warn_only=True):
            execute(
                product_install,
                'upstream',
                host=cls.vm.ip_addr
            )

    @classmethod
    def tearDownClass(cls):  # noqa
        super(InstallerTestCase, cls).tearDownClass()
        cls.vm.destroy()
