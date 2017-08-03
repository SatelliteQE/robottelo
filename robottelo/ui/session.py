# -*- encoding: utf-8 -*-
import logging
import os

from datetime import datetime
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.ui.factory import make_org
from robottelo.ui.browser import browser, DockerBrowser
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.bookmark import Bookmark
from robottelo.ui.computeprofile import ComputeProfile
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.configgroups import ConfigGroups
from robottelo.ui.container import Container
from robottelo.ui.contenthost import ContentHost
from robottelo.ui.contentviews import ContentViews
from robottelo.ui.dashboard import Dashboard
from robottelo.ui.discoveredhosts import DiscoveredHosts
from robottelo.ui.discoveryrules import DiscoveryRules
from robottelo.ui.dockertag import DockerTag
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.errata import Errata
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hardwaremodel import HardwareModel
from robottelo.ui.hostcollection import HostCollection
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.hosts import Hosts
from robottelo.ui.job import Job
from robottelo.ui.job_template import JobTemplate
from robottelo.ui.ldapauthsource import LdapAuthSource
from robottelo.ui.lifecycleenvironment import LifecycleEnvironment
from robottelo.ui.location import Location
from robottelo.ui.login import Login
from robottelo.ui.medium import Medium
from robottelo.ui.my_account import MyAccount
from robottelo.ui.navigator import Navigator
from robottelo.ui.operatingsys import OperatingSys
from robottelo.ui.org import Org
from robottelo.ui.oscapcontent import OpenScapContent
from robottelo.ui.oscappolicy import OpenScapPolicy
from robottelo.ui.oscapreports import OpenScapReports
from robottelo.ui.oscap_tailoringfile import OpenScapTailoringfile
from robottelo.ui.packages import Package
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.products import Products
from robottelo.ui.puppetclasses import PuppetClasses
from robottelo.ui.puppetmodule import PuppetModule
from robottelo.ui.registry import Registry
from robottelo.ui.repository import Repos
from robottelo.ui.rhai import RHAI
from robottelo.ui.role import Role
from robottelo.ui.settings import Settings
from robottelo.ui.scparams import SmartClassParameter
from robottelo.ui.smart_variable import SmartVariable
from robottelo.ui.subnet import Subnet
from robottelo.ui.subscription import Subscriptions
from robottelo.ui.sync import Sync
from robottelo.ui.syncplan import Syncplan
from robottelo.ui.task import Task
from robottelo.ui.template import Template
from robottelo.ui.trend import Trend
from robottelo.ui.usergroup import UserGroup
from robottelo.ui.user import User

_org_cache = {}
LOGGER = logging.getLogger(__name__)


class Session(object):
    """A session context manager that manages login and logout"""

    def __init__(self, test, user=None, password=None):
        self.test = test
        self._password = password
        self._user = user

    def __enter__(self):
        if settings.browser == 'docker':
            self._docker_browser = DockerBrowser(name=self.test.id())
            self._docker_browser.start()
            self.browser = self._docker_browser.webdriver
        else:
            self.browser = browser()

        # for compatibility purposes
        self.test.browser = self.browser

        self.browser.foreman_user = self.test.foreman_user
        self.browser.foreman_password = self.test.foreman_password

        if self._user is None:
            self._user = getattr(
                self.browser, 'foreman_user', settings.server.admin_username
            )

        if self._password is None:
            self._password = getattr(
                self.browser,
                'foreman_password',
                settings.server.admin_password
            )

        self.browser.maximize_window()
        self.browser.get(settings.server.get_url())
        # Workaround 'Certificate Error' screen on Microsoft Edge
        if (self.test.driver_name == 'edge' and
                'Certificate Error' in self.browser.title or
                'Login' not in self.browser.title):
            self.browser.get(
                "javascript:document.getElementById('invalidcert_continue')"
                ".click()"
            )

        self.test.addCleanup(
            self.test._saucelabs_test_result, self.browser.session_id)

        # Library methods
        self.activationkey = ActivationKey(self.browser)
        self.architecture = Architecture(self.browser)
        self.bookmark = Bookmark(self.browser)
        self.container = Container(self.browser)
        self.compute_profile = ComputeProfile(self.browser)
        self.compute_resource = ComputeResource(self.browser)
        self.contenthost = ContentHost(self.browser)
        self.configgroups = ConfigGroups(self.browser)
        self.content_views = ContentViews(self.browser)
        self.dashboard = Dashboard(self.browser)
        self.dockertag = DockerTag(self.browser)
        self.domain = Domain(self.browser)
        self.errata = Errata(self.browser)
        self.discoveredhosts = DiscoveredHosts(self.browser)
        self.discoveryrules = DiscoveryRules(self.browser)
        self.environment = Environment(self.browser)
        self.gpgkey = GPGKey(self.browser)
        self.hardwaremodel = HardwareModel(self.browser)
        self.hostcollection = HostCollection(self.browser)
        self.hostgroup = Hostgroup(self.browser)
        self.hosts = Hosts(self.browser)
        self.job = Job(self.browser)
        self.jobtemplate = JobTemplate(self.browser)
        self.ldapauthsource = LdapAuthSource(self.browser)
        self.lifecycleenvironment = LifecycleEnvironment(self.browser)
        self.location = Location(self.browser)
        self.login = Login(self.browser)
        self.medium = Medium(self.browser)
        self.my_account = MyAccount(self.browser)
        self.navigator = Navigator(self.browser)
        self.nav = self.navigator  # for compatibility purposes
        self.user = User(self.browser)
        self.operatingsys = OperatingSys(self.browser)
        self.org = Org(self.browser)
        self.oscapcontent = OpenScapContent(self.browser)
        self.oscappolicy = OpenScapPolicy(self.browser)
        self.oscapreports = OpenScapReports(self.browser)
        self.oscaptailoringfile = OpenScapTailoringfile(self.browser)
        self.package = Package(self.browser)
        self.partitiontable = PartitionTable(self.browser)
        self.puppetclasses = PuppetClasses(self.browser)
        self.puppetmodule = PuppetModule(self.browser)
        self.products = Products(self.browser)
        self.registry = Registry(self.browser)
        self.repository = Repos(self.browser)
        self.rhai = RHAI(self.browser)
        self.role = Role(self.browser)
        self.settings = Settings(self.browser)
        self.sc_parameters = SmartClassParameter(self.browser)
        self.smart_variable = SmartVariable(self.browser)
        self.subnet = Subnet(self.browser)
        self.subscriptions = Subscriptions(self.browser)
        self.sync = Sync(self.browser)
        self.syncplan = Syncplan(self.browser)
        self.task = Task(self.browser)
        self.template = Template(self.browser)
        self.trend = Trend(self.browser)
        self.usergroup = UserGroup(self.browser)

        # for compatibility purposes
        for attr in (
                'activationkey', 'architecture', 'bookmark', 'container',
                'compute_profile', 'compute_resource', 'contenthost',
                'configgroups', 'content_views', 'dashboard', 'dockertag',
                'domain', 'errata', 'discoveredhosts', 'discoveryrules',
                'environment', 'gpgkey', 'hardwaremodel', 'hostcollection',
                'hostgroup', 'hosts', 'job', 'jobtemplate', 'ldapauthsource',
                'lifecycleenvironment', 'location', 'login', 'medium',
                'my_account', 'navigator', 'nav', 'user', 'operatingsys',
                'org', 'oscapcontent', 'oscappolicy', 'oscapreports',
                'oscaptailoringfile', 'package', 'partitiontable',
                'puppetclasses', 'puppetmodule',
                'products', 'registry', 'repository', 'rhai', 'role',
                'settings', 'sc_parameters', 'smart_variable', 'subnet',
                'subscriptions', 'sync', 'syncplan', 'task', 'template',
                'trend', 'usergroup'):
            setattr(self.test, attr, getattr(self, attr))

        self.login.login(self._user, self._password)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.login.logout()
            else:
                self.take_screenshot()
        except Exception as err:
            LOGGER.exception(err)
        finally:
            if settings.browser == 'docker':
                self._docker_browser.stop()
            else:
                self.browser.quit()

    def take_screenshot(self):
        """Take screen shot from the current browser window.

        The screenshot named ``screenshot-YYYY-mm-dd_HH_MM_SS.png`` will be
        placed on the path specified by
        ``settings.screenshots_path/YYYY-mm-dd/ClassName/method_name/``.

        All directories will be created if they don't exist. Make sure that the
        user running robottelo have the right permissions to create files and
        directories matching the complete.
        """
        # Take a screenshot if any exception is raised and the test method is
        # not in the skipped tests.
        now = datetime.now()
        path = os.path.join(
            settings.screenshots_path,
            now.strftime('%Y-%m-%d'),
        )
        if not os.path.exists(path):
            os.makedirs(path)
        filename = '{0}-{1}-screenshot-{2}.png'.format(
            type(self.test).__name__,
            self.test._testMethodName,
            now.strftime('%Y-%m-%d_%H_%M_%S')
        )
        path = os.path.join(path, filename)
        LOGGER.debug('Saving screenshot %s', path)
        self.browser.save_screenshot(path)

    def get_org_name(self):
        """
        Make a Organization and cache its name to be returned through session,
        avoiding overhead of its recreation on each test.

        Organization Must be at same state (not mutate) at the end of the test

        Create your own organization if mutation is needed. Otherwise other
        tests can break with your tests side effects

        :return: str: Organization name
        """
        if 'org_name' in _org_cache:
            return _org_cache['org_name']
        org_name = gen_string('alpha')
        make_org(self, org_name=org_name)
        _org_cache['org_name'] = org_name
        return org_name
