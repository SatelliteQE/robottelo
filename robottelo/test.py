"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
 to help writting API, CLI and UI tests.

"""
import logging
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest
from robottelo.cli.metatest import MetaCLITest
from robottelo.common.helpers import get_server_url
from robottelo.common import conf
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.configgroups import ConfigGroups
from robottelo.ui.contentenv import ContentEnvironment
from robottelo.ui.contentviews import ContentViews
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
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
from robottelo.ui.usergroup import UserGroup
from robottelo.ui.user import User
from selenium_factory.SeleniumFactory import SeleniumFactory
from selenium import webdriver


SAUCE_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"


class TestCase(unittest.TestCase):
    """Robottelo test case"""

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        cls.logger = logging.getLogger('robottelo')


class APITestCase(TestCase):
    """Test case for API tests."""
    def assertIntersects(self, first, other, msg=None):
        assert_intersects(first, other, msg)


class CLITestCase(TestCase):
    """Test case for CLI tests."""

    @classmethod
    def setUpClass(cls):
        """
        Make sure that we only read configuration values once.
        """
        super(CLITestCase, cls).setUpClass()
        cls.hostname = conf.properties['main.server.hostname']
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.key_filename = conf.properties['main.server.ssh.key_private']
        cls.root = conf.properties['main.server.ssh.username']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['nosetests.verbosity'])

    def setUp(self):
        """
        Log test class and method name before each test.
        """
        self.logger.debug("Running test %s/%s", type(self).__name__,
                          self._testMethodName)


class MetaCLITestCase(CLITestCase):
    """
    All Test modules should inherit from MetaCLI in order to obtain default
    positive/negative CRUD tests.
    """
    __metaclass__ = MetaCLITest


class UITestCase(TestCase):
    """Test case for UI tests."""

    @classmethod
    def setUpClass(cls):
        """
        Make sure that we only read configuration values once.
        """
        super(UITestCase, cls).setUpClass()
        cls.katello_user = conf.properties['foreman.admin.username']
        cls.katello_passwd = conf.properties['foreman.admin.password']
        cls.driver_name = conf.properties['saucelabs.driver']
        cls.locale = conf.properties['main.locale']
        cls.verbosity = int(conf.properties['nosetests.verbosity'])
        cls.remote = int(conf.properties['main.remote'])

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
        self.browser.get(get_server_url())

        # Library methods
        self.activationkey = ActivationKey(self.browser)
        self.architecture = Architecture(self.browser)
        self.compute_resource = ComputeResource(self.browser)
        self.configgroups = ConfigGroups(self.browser)
        self.contentenv = ContentEnvironment(self.browser)
        self.content_views = ContentViews(self.browser)
        self.domain = Domain(self.browser)
        self.environment = Environment(self.browser)
        self.gpgkey = GPGKey(self.browser)
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
        self.user = User(self.browser)
        self.usergroup = UserGroup(self.browser)

    def tearDown(self):
        """
        Make sure to close the browser after each test.
        """

        self.browser.quit()
        self.browser = None


def assert_instance_intersects(first, other):
    """Determines if first and other match in type
    """
    r = not isinstance(first, type(other))
    r = r or not isinstance(other, type(first))

    if r:
        return (
            "!Types",
            type(first),
            type(other))
    return True


def assert_list_intersects(first, other):
    """Compares two lists, and determines,
    if each item in first intersects
    with at least one item in other
    """
    grievance = []
    for v in first:
        if not any(intersection(v, i) is True for i in other):
            grievance.append(v)
    if grievance == []:
        return True
    return ("!in", grievance, other)


def assert_dict_intersects(first, other):
    """Compares two dictionaries, and determines,
    if shared keys contain intersecting values
    """
    grievance = {}
    for k in first:
        if k in other:
            self_v = first[k]
            other_v = other[k]
            res = intersection(self_v, other_v)
            if res is not True:
                grievance[k] = res
    if grievance == {}:
        return True
    return ("!in", grievance)


def intersection(first, other):
    """Compares two objects to determine, if they share common information.
    Returns either true, or touple describing the difference

    >>> intersection("n1","n2")
    ('!=', 'n1', 'n2')
    >>> intersection([1,2,3,5],[2,1,0,2,3,4])
    ('!in', [5], [2, 1, 0, 2, 3, 4])
    >>> intersection({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":2,"e2":3})
    ('!in', {'s2': ('!=', 0, 2)})
    >>> intersection(
    ...     {"name":"n1","org":{"name":"o1"}},
    ...     {"name":"n1","org":{"name":"o2"}})
    ...
    ('!in', {'org': ('!in', {'name': ('!=', 'o1', 'o2')})})

    """
    if first is other:
        return True
    elif first == other:
        return True
    elif isinstance(first, type([])):
        return assert_list_intersects(first, other)
    elif hasattr(first, "__dict__") and hasattr(other, "__dict__"):
        self_data = first.__dict__
        other_data = other.__dict__
        return intersection(self_data, other_data)
    elif isinstance(first, type({})):
        return assert_dict_intersects(first, other)
    return ("!=", first, other)


def assert_intersects(first, other, msg=None):
    """Intersection based assert.
    """
    res = intersection(first, other)
    if res is not True:
        raise AssertionError(
            msg or "%r not intersects %r in %r" % (first, other, res)
            )


def is_intersecting(first, other):
    """Compares two objects to determine, if they share common information.
    Returns true or false.
    >>> is_intersecting("n1","n1")
    True
    >>> is_intersecting("n1","n2")
    False
    >>> is_intersecting([1,2,3],[2,1,0,2,3,4])
    True
    >>> is_intersecting([1,2,3,5],[2,1,0,2,3,4])
    False
    >>> is_intersecting({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":0,"e2":3},)
    True
    >>> is_intersecting({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":2,"e2":3},)
    False
    >>> class Test:
    ...     pass
    ...
    >>> t1 = Test()
    >>> t2 = Test()
    >>> t1.a = 1
    >>> t1.b = 1
    >>> t2.a = 1
    >>> t2.c = 2
    >>> is_intersecting(t1,t2)
    True
    """
    if intersection(first, other) is True:
        return True
    return False
