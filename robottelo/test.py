"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
to help writing API, CLI and UI tests.

"""
import csv
import logging
import os
import pytest
import re
import unittest2

try:
    import sauceclient
except ImportError:
    # Optional requirement, if installed robottelo will report results back to
    # saucelabs.
    sauceclient = None

from datetime import datetime
from fauxfactory import gen_string
from nailgun import entities
from robottelo import ssh
from robottelo.cleanup import EntitiesCleaner
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.org import Org as OrgCli
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG, DEFAULT_ORG_ID
from robottelo.performance.constants import NUM_THREADS
from robottelo.performance.graph import (
    generate_bar_chart_stat,
    generate_line_chart_raw_candlepin,
    generate_line_chart_stat_bucketized_candlepin,
)
from robottelo.performance.stat import generate_stat_for_concurrent_thread
from robottelo.performance.thread import (
    DeleteThread,
    SyncThread,
    SubscribeAKThread,
    SubscribeAttachThread
)
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
from robottelo.ui.packages import Package
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.products import Products
from robottelo.ui.puppetclasses import PuppetClasses
from robottelo.ui.registry import Registry
from robottelo.ui.repository import Repos
from robottelo.ui.rhai import RHAI
from robottelo.ui.role import Role
from robottelo.ui.settings import Settings
from robottelo.ui.smart_variable import SmartVariable
from robottelo.ui.subnet import Subnet
from robottelo.ui.subscription import Subscriptions
from robottelo.ui.sync import Sync
from robottelo.ui.syncplan import Syncplan
from robottelo.ui.systemgroup import SystemGroup
from robottelo.ui.template import Template
from robottelo.ui.trend import Trend
from robottelo.ui.usergroup import UserGroup
from robottelo.ui.user import User


LOGGER = logging.getLogger(__name__)


class NotRaisesValueHandler(object):
    """Base class for handling exception values for AssertNotRaises. Child
    classes can be used to validate whether specific for interface expected
    value is present in exception.
    """

    def validate(self, exception):
        """Validate whether expected value is present in exception."""
        raise NotImplemented()

    @property
    def value_name(self):
        """Property used to return expected value name (e.g. 'status code' or
        'return code').
        """
        raise NotImplemented()


class APINotRaisesValueHandler(NotRaisesValueHandler):
    """AssertNotRaises value handler for API status code."""

    def __init__(self, expected_value):
        """Store expected status code."""
        self.expected_value = expected_value

    def validate(self, exception):
        """Validate whether expected status code is present in specific
        exception.
        """
        return (
            True if self.expected_value == exception.response.status_code
            else False
        )

    @property
    def value_name(self):
        """Returns API expected value name (status code)"""
        return 'HTTP status code'


class CLINotRaisesValueHandler(NotRaisesValueHandler):
    """AssertNotRaises value handler for CLI return code."""

    def __init__(self, expected_value):
        """Store expected return code"""
        self.expected_value = expected_value

    def validate(self, exception):
        """Validate whether expected return code is present in specific
        exception.
        """
        return (
            True if self.expected_value == exception.return_code
            else False
        )

    @property
    def value_name(self):
        """Returns CLI expected value name (return code)"""
        return 'return code'


class _AssertNotRaisesContext(object):
    """A context manager used to implement :meth:`TestCase.assertNotRaises`.
    """

    def __init__(self, expected, test_case, expected_regex=None,
                 expected_value=None, value_handler=None):
        self.expected = expected
        self.expected_regex = expected_regex
        self.value_handler = value_handler
        if value_handler is None and expected_value:
            self.value_handler = test_case._default_notraises_value_handler(
                expected_value)
        self.failureException = test_case.failureException

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            return True

        try:
            exc_name = self.expected.__name__
        except AttributeError:
            exc_name = str(self.expected)

        self.exception = exc_value  # store for later retrieval

        if issubclass(exc_type, self.expected):
            if not any((self.value_handler, self.expected_regex)):
                raise self.failureException(
                    "{0} raised".format(exc_name))
            regex = self.expected_regex
            response_code = None
            if self.value_handler:
                response_code = self.value_handler.validate(exc_value)
            if regex:
                regex = True if regex.search(str(exc_value)) else False

            if response_code and regex:
                raise self.failureException(
                    "{0} raised with {1} {2} and {3} found in {4}"
                    .format(
                        exc_name,
                        self.value_handler.value_name,
                        self.value_handler.expected_value,
                        self.expected_regex.pattern,
                        str(exc_value),
                    )
                )
            elif response_code and regex is None:
                raise self.failureException(
                    "{0} raised with {1} {2}".format(
                        exc_name,
                        self.value_handler.value_name,
                        self.value_handler.expected_value,
                    )
                )
            elif regex and response_code is None:
                raise self.failureException(
                    "{0} raised and {1} found in {2}".format(
                        exc_name,
                        self.expected_regex.pattern,
                        str(exc_value),
                    )
                )
            else:
                # pass through
                return False

        else:
            # pass through
            return False


class TestCase(unittest2.TestCase):
    """Robottelo test case"""

    _default_notraises_value_handler = None

    @pytest.fixture(autouse=True)
    def _set_worker_logger(self, worker_id):
        """Set up a separate logger for each pytest-xdist worker
        if worker_id != 'master' then xdist is running in multi-threading so
        a logfile named 'robottelo_gw{worker_id}.log' will be created.
        """
        self.worker_id = worker_id
        if worker_id != 'master':
            if '{0}'.format(worker_id) not in [
                    h.get_name() for h in self.logger.handlers]:
                formatter = logging.Formatter(
                    fmt='%(asctime)s - {0} - %(name)s - %(levelname)s -'
                    ' %(message)s'.format(worker_id),
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                handler = logging.FileHandler(
                    'robottelo_{0}.log'.format(worker_id))
                handler.set_name('{0}'.format(worker_id))
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                # Nailgun HTTP logs should also be included in gw* logs
                logging.getLogger('nailgun').addHandler(handler)

    @classmethod
    def setUpClass(cls):  # noqa
        super(TestCase, cls).setUpClass()
        if not settings.configured:
            settings.configure()
        cls.logger = logging.getLogger('robottelo')
        cls.logger.debug('Started setUpClass: {0}/{1}'.format(
            cls.__module__, cls.__name__))
        # NOTE: longMessage defaults to True in Python 3.1 and above
        cls.longMessage = True
        cls.foreman_user = settings.server.admin_username
        cls.foreman_password = settings.server.admin_password
        if settings.cleanup:
            cls.cleaner = EntitiesCleaner(
                entities.Organization,
                entities.Host,
                entities.HostGroup
            )

    @classmethod
    def tearDownClass(cls):
        cls.logger.debug('Started tearDownClass: {0}/{1}'.format(
            cls.__module__, cls.__name__))
        if settings.cleanup:
            cls.cleaner.clean()

    def setUp(self):
        """setup for tests"""
        self.log_method_name(prefix='Started Test: ')

    def tearDown(self):
        """teardown for tests"""
        self.log_method_name(prefix='Finished Test: ')

    def log_method_name(self, prefix=None):
        """Log test method name"""
        self.logger.debug('{0}{1}/{2}'.format(
            prefix,
            type(self).__name__,
            self._testMethodName,
        ))

    def assertNotRaises(self, expected_exception, callableObj=None,
                        expected_value=None, value_handler=None, *args,
                        **kwargs):
        """Fail if an exception of class expected_exception is raised by
        callableObj when invoked with specified positional and keyword
        arguments. If a different type of exception is raised, it will not be
        caught, and the test case will be deemed to have suffered an error,
        exactly as for an unexpected exception.

        If called with callableObj omitted or None, will return a context
        object used like this::

                with self.assertNotRaises(SomeException):
                    do_something()

        The context manager keeps a reference to the exception as the
        'exception' attribute. This allows you to inspect the exception after
        the assertion::

               with self.assertNotRaises(SomeException) as cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 1)

        In addition, optional 'http_status_code' or 'cli_return_code' arg may
        be passed. This allows to specify exact HTTP status code or CLI return
        code, returned by ``requests.HTTPError`` or
        :class:`robottelo.cli.base.CLIReturnCodeError` accordingly, which
        should be validated. In such case only expected exception with expected
        response code will be caught.
        """
        context = _AssertNotRaisesContext(
            expected_exception,
            self,
            expected_value=expected_value,
            value_handler=value_handler,
        )
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)

    def assertNotRaisesRegex(self, expected_exception, expected_regex,
                             callableObj=None, expected_value=None,
                             value_handler=None, *args, **kwargs):
        """Fail if an exception of class expected_exception is raised and the
        message in the exception matches a regex.
        """
        if expected_regex is not None:
            expected_regex = re.compile(expected_regex)
        context = _AssertNotRaisesContext(
            expected_exception,
            self,
            expected_regex=expected_regex,
            expected_value=expected_value,
            value_handler=value_handler,
        )
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)


class APITestCase(TestCase):
    """Test case for API tests."""
    _default_notraises_value_handler = APINotRaisesValueHandler
    _multiprocess_can_split_ = True


class CLITestCase(TestCase):
    """Test case for CLI tests."""
    _default_notraises_value_handler = CLINotRaisesValueHandler
    _multiprocess_can_split_ = True


class UITestCase(TestCase):
    """Test case for UI tests."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Make sure that we only read configuration values once."""
        super(UITestCase, cls).setUpClass()
        cls.set_session_org()
        cls.set_session_user()
        if cls.session_user is not None:
            cls.foreman_user = cls.session_user.login
        cls.driver_name = settings.webdriver
        cls.driver_binary = settings.webdriver_binary
        cls.locale = settings.locale
        cls.server_name = settings.server.hostname
        cls.logger.info(
            u'Session set with:\n'
            u'\tUser: {cls.session_user.id}:{cls.session_user.login}\n'
            u'\tOrganization: {cls.session_org.id}:{cls.session_org.name}\n'
            u'\tWeb Driver: {cls.driver_name}\n'
            u'\tBinary: {cls.driver_binary}\n'
            u'\tLocale: {cls.locale}\n'
            u'\tServer Name: {cls.server_name}'
            .format(cls=cls)
        )

    @classmethod
    def set_session_org(cls):
        """TestCases can overwrite this method to create a different
        organization object for the session.
        """
        cls.session_org = entities.Organization(
            id=DEFAULT_ORG_ID, name=DEFAULT_ORG
        )

    @classmethod
    def set_session_user(cls):
        """Creates a new user for each session this method can be overwritten
        in TestCases in order to get different default user
        """
        try:
            username = gen_string('alpha')
            cls.session_user = entities.User(
                firstname='Robottelo User {0}'.format(username),
                login=username,
                password=cls.foreman_password,
                admin=True,
                default_organization=cls.session_org
            ).create()
        except Exception as e:
            cls.session_user = None
            cls.logger.warn('Unable to create session_user: %s', str(e))

    @classmethod
    def tearDownClass(cls):
        super(UITestCase, cls).tearDownClass()
        cls.delete_session_user()

    @classmethod
    def delete_session_user(cls):
        """Delete created session user can be overwritten in TestCase to
        bypass user deletion
        """
        if cls.session_user is not None:
            try:
                cls.session_user.delete(synchronous=False)
            except Exception as e:
                cls.logger.warn('Unable to delete session_user: %s', str(e))
            else:
                cls.logger.info(
                    'Session user is being deleted: %s', cls.session_user)

    def setUp(self):  # noqa
        """We do want a new browser instance for every test."""
        super(UITestCase, self).setUp()
        if settings.browser == 'docker':
            self._docker_browser = DockerBrowser()
            self._docker_browser.start()
            self.browser = self._docker_browser.webdriver
            self.addCleanup(self._docker_browser.stop)
        else:
            self.browser = browser()
            self.addCleanup(self.browser.quit)
        self.browser.maximize_window()
        self.browser.get(settings.server.get_url())

        self.browser.foreman_user = self.foreman_user
        self.browser.foreman_password = self.foreman_password

        self.addCleanup(self._saucelabs_test_result)
        self.addCleanup(self.take_screenshot)

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
        self.user = User(self.browser)
        self.operatingsys = OperatingSys(self.browser)
        self.org = Org(self.browser)
        self.oscapcontent = OpenScapContent(self.browser)
        self.oscappolicy = OpenScapPolicy(self.browser)
        self.oscapreports = OpenScapReports(self.browser)
        self.package = Package(self.browser)
        self.partitiontable = PartitionTable(self.browser)
        self.puppetclasses = PuppetClasses(self.browser)
        self.products = Products(self.browser)
        self.registry = Registry(self.browser)
        self.repository = Repos(self.browser)
        self.rhai = RHAI(self.browser)
        self.role = Role(self.browser)
        self.settings = Settings(self.browser)
        self.smart_variable = SmartVariable(self.browser)
        self.subnet = Subnet(self.browser)
        self.subscriptions = Subscriptions(self.browser)
        self.sync = Sync(self.browser)
        self.syncplan = Syncplan(self.browser)
        self.systemgroup = SystemGroup(self.browser)
        self.template = Template(self.browser)
        self.trend = Trend(self.browser)
        self.user = User(self.browser)
        self.usergroup = UserGroup(self.browser)

    def take_screenshot(self):
        """Take screen shot from the current browser window.

        The screenshot named ``screenshot-YYYY-mm-dd_HH_MM_SS.png`` will be
        placed on the path specified by
        ``settings.screenshots_path/YYYY-mm-dd/ClassName/method_name/``.

        All directories will be created if they don't exist. Make sure that the
        user running robottelo have the right permissions to create files and
        directories matching the complete.
        """
        if (len(self._outcome.errors) > 0 and
                self in self._outcome.errors[-1]):
            # Take screenshot if any exception is raised and the test method is
            # not in the skipped tests.
            now = datetime.now()
            path = os.path.join(
                settings.screenshots_path,
                now.strftime('%Y-%m-%d'),
            )
            if not os.path.exists(path):
                os.makedirs(path)
            filename = '{0}-{1}-screenshot-{2}.png'.format(
                type(self).__name__,
                self._testMethodName,
                now.strftime('%Y-%m-%d_%H_%M_%S')
            )
            path = os.path.join(path, filename)
            LOGGER.debug('Saving screenshot %s', path)
            self.browser.save_screenshot(path)

    def _saucelabs_test_result(self):
        """SauceLabs has no way to determine whether test passed or failed
        automatically, so we explicitly 'tell' it
        """
        if settings.browser == 'saucelabs' and sauceclient:
            sc = sauceclient.SauceClient(
                settings.saucelabs_user, settings.saucelabs_key)
            passed = True
            status = 'passed'
            if (len(self._outcome.errors) > 0 and
                    self in self._outcome.errors[-1]):
                passed = False
                status = 'failed'
            if (len(self._outcome.skipped) > 0 and
                    self in self._outcome.skipped[-1]):
                passed = None
                status = 'complete'
            LOGGER.debug(
                'Updating SauceLabs job "%s": name "%s" and status "%s"',
                self.browser.session_id,
                str(self),
                status
            )
            sc.jobs.update_job(
                self.browser.session_id, name=str(self), passed=passed)


class ConcurrentTestCase(TestCase):
    """Test utilities for writing performance tests.

    Define ConcurrentTestCase as base class of performance test case:

    1. concurrent subscription by AK,
    2. concurrent subscription by register and attach,
    3. concurrent subscription deletion.

    """

    @classmethod
    def setUpClass(cls):
        """Make sure to only read configuration values once."""
        super(ConcurrentTestCase, cls).setUpClass()

        # general running parameters
        cls.num_threads = NUM_THREADS
        cls.num_buckets = settings.performance.csv_buckets_count
        cls.vm_list = settings.performance.virtual_machines
        cls.org_id = cls._get_organization_id()  # get organization-id
        cls.sub_id = ''
        cls.num_iterations = 0     # depend on # of threads or clients
        cls.bucket_size = 0        # depend on # of iterations on each thread

        cls._convert_to_numbers()  # read in string type, convert to numbers

        # read default organization from constant module
        cls.default_org = DEFAULT_ORG

    @classmethod
    def _convert_to_numbers(cls):
        """read in string type series, convert to numbers"""
        cls.num_threads = [int(x) for x in cls.num_threads.split(',')]
        cls.num_buckets = int(cls.num_buckets)

    @classmethod
    def _set_testcase_parameters(
            cls,
            savepoint_name,
            raw_file_name,
            stat_file_name,
            raw_reg=None,
            stat_reg=None):
        """Set file names of raw and statistics .csv output

        Each file name is read from ``robottelo.constants``

        For subscription by activationKey or deletion case, would output:

        1. raw data file for ak/del:  raw_file_name.csv
        2. stat data file for ak/del: stat_file_name.csv

        For subscription by register and attach case, would output:
        1. raw data file for register:  reg_raw_file_name.csv
        2. raw data file for attach:    raw_file_name.csv
        3. stat data file for register: reg_stat_file_name.csv
        4. stat data file for attach:   stat_file_name.csv

        That is, set extra filenames for register step;
        while attach step would still output raw/stat_file_name.csv

        """
        # note: set savepoint empty to continue test without restore
        if savepoint_name == 'enabled_repos':
            cls.savepoint = settings.performance.enabled_repos_savepoint
        elif savepoint_name == 'fresh_install':
            cls.savepoint = settings.performance.fresh_install_savepoint
        else:
            cls.savepoint = ''
        cls.raw_file_name = raw_file_name
        cls.stat_file_name = stat_file_name

        if raw_reg is not None and stat_reg is not None:
            cls.reg_raw_file_name = raw_reg
            cls.reg_stat_file_name = stat_reg

    @classmethod
    def _get_organization_id(cls):
        """Get organization id"""
        try:
            result = OrgCli.list(per_page=False)
        except CLIReturnCodeError:
            cls.logger.error('Fail to get organization id.')
            raise RuntimeError('Invalid organization id. Stop!')
        return result[0]['id']

    def setUp(self):
        self.logger.debug(
            'Running test %s/%s', type(self).__name__, self._testMethodName)

        # Restore database before concurrent subscription/deletion
        self._restore_from_savepoint(self.savepoint)

    def _restore_from_savepoint(self, savepoint):
        """Restore from savepoint"""
        if savepoint == '':
            self.logger.warning('No savepoint while continuing test!')
            return
        self.logger.info('Reset db from /home/backup/{0}'.format(savepoint))
        ssh.command('./reset-db.sh /home/backup/{0}'.format(savepoint))

    def _get_subscription_id(self):
        """Get subscription id"""
        try:
            result = Subscription.list(
                {'organization-id': self.org_id},
                per_page=False
            )
        except CLIReturnCodeError:
            self.logger.error('Fail to get subscription id!')
            raise RuntimeError('Invalid subscription id. Stop!')
        subscription_id = result[0]['id']
        subscription_name = result[0]['name']
        self.logger.info(
            'Subscribed to {0} with subscription id {1}'
            .format(subscription_name, subscription_id)
        )
        return subscription_id, subscription_name

    def _set_num_iterations(self, total_iterations, current_num_threads):
        """Set # of iterations each thread will conduct.

        :param int total_iterations: total # of iterations for a test case
        :param int current_num_threads: number of clients or threads

        Example:

        1. split 5k total_iterations evenly between 10 clients, thus each
           client would conduct 500 iterations concurrently;
        2. split 6k evenly between 6 clients, thus each client would conduct
           1000 iterations concurrently;

        """
        self.num_iterations = total_iterations / current_num_threads

    def _set_bucket_size(self):
        """Set size for each bucket"""
        bucket = self.num_iterations / self.num_buckets

        # check if num_iterations for each client is smaller than 10
        if bucket > 0:
            self.bucket_size = bucket
        else:
            self.bucket_size = 1

    def _join_all_threads(self, thread_list):
        """Wait for all threads to complete"""
        for thread in thread_list:
            thread.join()

    def _get_output_filename(self, file_name):
        """Get type of test: ak/att/del/reg as output file name

        Extract type of test cases, thus differentiate output
        charts and csv files.

        :param str file_name: File name is value of ``self.raw_file_name``
            or ``self.stat_file_name``. For example:
            file_name = 'perf-raw-activationKey.csv'
        :return: file name before dot. For example: 'perf-raw-activationKey'
        :rtype str

        """
        split_file_name = file_name.split('.')
        return split_file_name[0]

    def _write_raw_csv_file(
            self,
            raw_file_name,
            time_result_dict,
            current_num_threads,
            test_case_name):
        """Write csv and chart for raw data of Candlepin Tests ak/att/del/reg

        Common method shared by three test cases:

        1. concurrent subscription by activation key
        2. concurrent subscription by attatch and register
        3. concurrent deletion

        Each step (activationKey, attach, delete & register) would output
        both csv and charts for raw data.

        :param str raw_file_name: The name of output raw csv file. The value
            is read from ``robottelo.constants`` but set by each test case
            using function ``_set_testcase_parameters`` defined in this module
        :param dict time_result_dict: The storage of all 5k timing values
        :param int current_num_threads: The number of threads/clients
        :param str test_case_name: The type of test case, set by function
            ``_get_output_filename`` defined in this module

        """
        self.logger.debug(
            'Timing result is: {0}'.format(time_result_dict))

        with open(raw_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # for each thread, write its head and data
            for i in range(current_num_threads):
                writer.writerow(time_result_dict.get('thread-{0}'.format(i)))
            writer.writerow([])

        # generate line chart of raw data
        test_category = self._get_output_filename(raw_file_name)
        generate_line_chart_raw_candlepin(
            time_result_dict,
            'Candlepin Subscription Raw Timings Line Chart - '
            '({0}-{1}-clients)'
            .format(test_category, current_num_threads),
            '{0}-{1}-clients-raw-data-line-chart.svg'
            .format(test_category, current_num_threads)
        )

    def _write_stat_csv_chart(
            self,
            stat_file_name,
            time_result_dict,
            current_num_threads,
            test_case_name):
        """Compute stat of ak/att/del/reg and generate charts

        Common method shared by three test cases:

        1. concurrent subscription by activation key
        2. concurrent subscription by attatch and register
        3. concurrent deletion

        Each step (activationKey, attach, delete & register) would compute
        statistics, generate output as csv files and visualization of
        charts

        :param str stat_file_name: The name of output csv file. The value
            is read from ``robottelo.constants`` but set by each test case
            using function ``_set_testcase_parameters`` defined in this module
        :param dict time_result_dict: The storage of all 5k timing values
        :param int current_num_threads: The number of threads/clients
        :param str test_case_name: The type of test case, set by function
            ``_get_output_filename`` defined in this module

        """
        with open(stat_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # 1. write stat-per-client-bucketized result of ak/del/att/reg
            writer.writerow(['stat-per-client-bucketized'])
            self._write_stat_per_client_bucketized(
                stat_file_name,
                time_result_dict,
                current_num_threads,
            )
            writer.writerow([])

            # 2. write stat-per-test-bucketized result of ak/del/att/reg
            writer.writerow(['stat-per-test-bucketized'])
            self._write_stat_per_test_bucketized(
                stat_file_name,
                time_result_dict,
            )
            writer.writerow([])

            # 3. write stat-per-client result of ak/del/att
            writer.writerow(['stat-per-client'])
            self._write_stat_per_client(
                stat_file_name,
                time_result_dict,
                current_num_threads,
            )
            writer.writerow([])

            # 4. write stat-per-test result of ak/del/att
            writer.writerow(['stat-per-test'])
            self._write_stat_per_test(
                stat_file_name,
                time_result_dict,
            )
            writer.writerow([])

    def _write_stat_per_client_bucketized(
            self,
            stat_file_name,
            time_result_dict,
            current_num_threads):
        """Write bucketized stat of per-client results to csv file

        note: each bucket is just a split of a client i. For example::

            Input: # of clients = 1
            {thread-i: [(50 data) | (50 data)|...]}
            Output:
            line chart of statistics on these buckets.

        """
        test_category = self._get_output_filename(stat_file_name)

        for i in range(current_num_threads):
            time_list = time_result_dict.get('thread-{0}'.format(i))
            thread_name = 'client-{0}'.format(i)
            stat_dict = generate_stat_for_concurrent_thread(
                thread_name,
                time_list,
                stat_file_name,
                self.bucket_size,
                self.num_buckets
            )

            # create line chart with each client being grouped by buckets
            generate_line_chart_stat_bucketized_candlepin(
                stat_dict,
                'Concurrent Subscription Statistics - per client bucketized: '
                'Client-{0} by {1}-{2}-clients'
                .format(i, test_category, current_num_threads),
                '{0}-client-{1}-bucketized-{2}-clients.svg'
                .format(test_category, i, current_num_threads),
                self.bucket_size,
                self.num_buckets
            )

    def _write_stat_per_test_bucketized(
            self,
            stat_file_name,
            time_result_dict):
        """Write bucketized stat of per-test to csv file

        note: each bucket of all clients would merge into a chunk;
        generate stat for each such chunk. For example::

            Input: # of clients = 10
            thread-0: [(50 data) | (50 data)|...]
            thread-1: [(50 data) | (50 data)|...]
            ...
            thread-9: [(50 data) | (50 data)|...]
            Output:
            sublist [500 data grouped from all clients' first buckets],
                    [500 data grouped from all clients' next buckets],
                    ...
                    [500 data grouped from all clients' last buckets];
            line chart of statistics on these chunks.

        """
        # parameters for generating bucketized line chart
        stat_dict = {}
        return_stat = {}
        current_num_threads = len(time_result_dict)
        test_category = self._get_output_filename(stat_file_name)

        for i in range(self.num_buckets):
            chunks_bucket_i = []
            for j in range(len(time_result_dict)):
                time_list = time_result_dict.get('thread-{0}'.format(j))
                # slice out bucket-size from each client's result and merge
                chunks_bucket_i += time_list[
                    i * self.bucket_size: (i + 1) * self.bucket_size
                ]

            # for each chunk i, compute and output its stat
            return_stat = generate_stat_for_concurrent_thread(
                'bucket-{0}'.format(i),
                chunks_bucket_i,
                stat_file_name,
                len(chunks_bucket_i),
                1
            )

            # for each chunk i, add stat into final return_dict
            stat_dict.update({i: return_stat.get(0, (0, 0, 0, 0))})

        # create line chart with all clients grouped by a chunk of buckets
        generate_line_chart_stat_bucketized_candlepin(
            stat_dict,
            'Concurrent Subscription Statistics - per test bucketized: '
            '({0}-{1}-clients)'
            .format(test_category, current_num_threads),
            '{0}-test-bucketized-{1}-clients.svg'
            .format(test_category, current_num_threads),
            self.bucket_size,
            self.num_buckets
        )

    def _write_stat_per_client(
            self,
            stat_file_name,
            time_result_dict,
            current_num_threads):
        """Write stat of per-client results to csv file

        note: take the full list of a client i; calculate stat on the list

        """
        # parameters for generating bucketized line chart
        stat_dict = {}
        return_stat = {}
        current_num_threads = len(time_result_dict)
        test_category = self._get_output_filename(stat_file_name)

        for i in range(current_num_threads):
            time_list = time_result_dict.get('thread-{0}'.format(i))
            thread_name = 'client-{0}'.format(i)

            # for each client i, compute and output its stat
            return_stat = generate_stat_for_concurrent_thread(
                thread_name,
                time_list,
                stat_file_name,
                len(time_list),
                1
            )

            # for each chunk i, add stat into final return_dict
            stat_dict.update({i: return_stat.get(0, (0, 0, 0, 0))})

        # create graph based on stats of all clients
        generate_bar_chart_stat(
            stat_dict,
            'Concurrent Subscription Statistics - per client: '
            '({0}-{1}-clients)'
            .format(test_category, current_num_threads),
            '{0}-per-client-{1}-clients.svg'
            .format(test_category, current_num_threads),
            'client'
        )

    def _write_stat_per_test(self, stat_file_name, time_result_dict):
        """Write stat of per-test results to csv file

        note: take the full dictionary of test and calculate overall stat

        """
        full_list = []  # list containing 1st to 5kth data point
        current_num_threads = len(time_result_dict)
        test_category = self._get_output_filename(stat_file_name)

        for i in range(len(time_result_dict)):
            time_list = time_result_dict.get('thread-{0}'.format(i))
            full_list += time_list

        stat_dict = generate_stat_for_concurrent_thread(
            'test-{0}'.format(len(time_result_dict)),
            full_list,
            stat_file_name,
            len(full_list),
            1
        )

        generate_bar_chart_stat(
            stat_dict,
            'Concurrent Subscription Statistics - per test: '
            '({0}-{1}-clients)'
            .format(test_category, current_num_threads),
            '{0}-per-test-{1}-clients.svg'
            .format(test_category, current_num_threads),
            'test'
        )

    def kick_off_ak_test(self, current_num_threads, total_iterations):
        """Refactor out concurrent register by ak test case

        :param int current_num_threads: number of threads
        :param int total_iterations: # of iterations a test case would run

        """
        # check if number of threads are mapped with number of vms
        current_vm_list = self.vm_list[:current_num_threads]
        self.assertEqual(len(current_vm_list), current_num_threads)

        # Parameter for statistics files
        self._set_num_iterations(total_iterations, current_num_threads)
        self._set_bucket_size()

        # Create a list to store all threads
        thread_list = []
        # Create a dictionary to store all timing results from each client
        time_result_dict_ak = {}

        # Create new threads and start each thread mapped with a vm
        for i in range(current_num_threads):
            thread_name = 'thread-{0}'.format(i)
            time_result_dict_ak[thread_name] = []
            thread = SubscribeAKThread(
                i,
                thread_name,
                time_result_dict_ak,
                self.num_iterations,
                self.ak_name,
                self.default_org,
                current_vm_list[i]
            )
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of activation-key
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict_ak,
            current_num_threads,
            'raw-ak-{0}-clients'.format(current_num_threads)
        )

        # write stat result of ak and generate charts
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_ak,
            current_num_threads,
            'stat-ak-{0}-clients'.format(current_num_threads)
        )

    def kick_off_att_test(self, current_num_threads, total_iterations):
        """Refactor out concurrent register and attach test case

        :param int current_num_threads: number of threads
        :param int total_iterations: # of deletions a test case would run

        """
        # check if number of threads are mapped with number of vms
        current_vm_list = self.vm_list[:current_num_threads]
        self.assertEqual(len(current_vm_list), current_num_threads)

        # Parameter for statistics files
        self._set_num_iterations(total_iterations, current_num_threads)
        self._set_bucket_size()

        # Create a list to store all threads
        thread_list = []
        # Create a dictionary to store register timings from each client
        time_result_dict_register = {}
        # Create a dictionary to store attach timings from each client
        time_result_dict_attach = {}

        # Create new threads and start each thread mapped with a vm
        for i in range(current_num_threads):
            thread_name = 'thread-{0}'.format(i)
            time_result_dict_register[thread_name] = []
            time_result_dict_attach[thread_name] = []

            thread = SubscribeAttachThread(
                i,
                thread_name,
                {},
                time_result_dict_register,
                time_result_dict_attach,
                self.num_iterations,
                self.sub_id,
                self.default_org,
                self.environment,
                current_vm_list[i]
            )
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of register
        self._write_raw_csv_file(
            self.reg_raw_file_name,
            time_result_dict_register,
            current_num_threads,
            'raw-reg-{0}-clients'.format(current_num_threads)
        )

        # write raw result of attach
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict_attach,
            current_num_threads,
            'raw-att-{0}-clients'.format(current_num_threads)
        )

        # write stat result of register and generate charts
        self._write_stat_csv_chart(
            self.reg_stat_file_name,
            time_result_dict_register,
            current_num_threads,
            'stat-reg-{0}-clients'.format(current_num_threads)
        )

        # write stat result of attach and generate charts
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_attach,
            current_num_threads,
            'stat-att-{0}-clients'.format(current_num_threads)
        )

    def kick_off_del_test(self, current_num_threads):
        """Refactor out concurrent system deletion test case

        :param int current_num_threads: number of threads

        """
        # Get list of all uuids of registered systems

        self.logger.info('Retrieve list of uuids of all registered systems:')
        uuid_list = self._get_registered_uuids()

        # Parameter for statistics files
        total_iterations = len(uuid_list)

        self._set_num_iterations(total_iterations, current_num_threads)
        self._set_bucket_size()

        # Create a list to store all threads
        thread_list = []
        # Create a dictionary to store all timing results from each thread
        time_result_dict_del = {}

        # Create new threads and start the thread which has sublist of uuids
        for i in range(current_num_threads):
            time_result_dict_del['thread-{0}'.format(i)] = []
            thread = DeleteThread(
                i,
                'thread-{0}'.format(i),
                uuid_list[
                    self.num_iterations * i: self.num_iterations * (i + 1)
                ],
                time_result_dict_del
            )
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of del
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict_del,
            current_num_threads,
            'raw-del-{0}-clients'.format(current_num_threads)
        )

        # write stat result of del
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_del,
            current_num_threads,
            'stat-del-{0}-clients'.format(current_num_threads)
        )

    def kick_off_concurrent_sync_test(
            self,
            current_num_threads,
            is_initial_sync):
        """Refactor out concurrent repository synchronization test case

        :param int current_num_threads: The number of threads
        :param bool is_initial_sync: Decide whether resync or initial sync
        :return dict time_result_dict: Contain a list of X # of timings

        """
        self.logger.debug(
            'Concurrent Synchronize by {0} threads'
            .format(current_num_threads)
        )
        # determine the target repositories' names by configuration
        # sync only a sublist of target repos for each test case
        repo_names_list = self.repo_names_list[:current_num_threads]
        self.logger.debug(
            'Targeting repositories to sync: {0}'
            .format(repo_names_list)
        )

        # Create a list to store all threads
        thread_list = []
        # Create a dictionary to store all timing results from each thread
        time_result_dict = {}
        for thread_id in range(current_num_threads):
            time_result_dict['thread-{0}'.format(thread_id)] = []

        # sync all specified repositories and repeate X times
        for iteration in range(self.sync_iterations):
            # for each thread, sync a single repository
            for tid in range(current_num_threads):
                repo_name = repo_names_list[tid]
                repo_id = self.map_repo_name_id.get(repo_name, None)

                if repo_id is None:
                    self.logger.warning('Invalid repository name!')
                    continue

                self.logger.debug(
                    '{0} repository {1} attempt {2} '
                    'on {3}-repo test case starts:'
                    .format(
                        'Initially sync' if is_initial_sync else 'Resync',
                        repo_name,
                        iteration,
                        current_num_threads
                    )
                )

                thread = SyncThread(
                    tid,
                    "thread-{0}".format(tid),
                    time_result_dict,
                    repo_id,
                    repo_name,
                    iteration,
                )
                thread.start()
                thread_list.append(thread)

            # wait all threads in thread list
            self._join_all_threads(thread_list)

            # Once all threads have completed syncs,
            # reset database before next iteration, if initial sync test
            if is_initial_sync:
                self.logger.debug(
                    'Reset database for Initial Sync test '
                    'on {0}-repo test case attempt {1}'
                    .format(current_num_threads, iteration)
                )
                self._restore_from_savepoint(self.savepoint)
            else:
                self.logger.debug(
                    'Resync on {0}-repo test case attempt {1} completes'
                    .format(current_num_threads, iteration)
                )

        return time_result_dict
