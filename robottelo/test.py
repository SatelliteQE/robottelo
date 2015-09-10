"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
to help writing API, CLI and UI tests.

"""
import csv
import logging
import os
import signal
import sys
import unittest

from datetime import datetime
from robottelo import ssh
from robottelo.cli.metatest import MetaCLITest
from robottelo.cli.org import Org as OrgCli
from robottelo.cli.subscription import Subscription
from robottelo.config import conf
from robottelo.helpers import get_server_url
from robottelo.performance.constants import(
    DEFAULT_ORG,
    NUM_THREADS,
)
from robottelo.performance.graph import(
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
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.computeprofile import ComputeProfile
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.configgroups import ConfigGroups
from robottelo.ui.contentenv import ContentEnvironment
from robottelo.ui.contentviews import ContentViews
from robottelo.ui.contentsearch import ContentSearch
from robottelo.ui.discoveryrules import DiscoveryRules
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hardwaremodel import HardwareModel
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.hosts import Hosts
from robottelo.ui.ldapauthsource import LdapAuthSource
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
from robottelo.ui.rhai import RHAI
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
from selenium import webdriver
from selenium_factory.SeleniumFactory import SeleniumFactory

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
        self.compute_profile = ComputeProfile(self.browser)
        self.compute_resource = ComputeResource(self.browser)
        self.configgroups = ConfigGroups(self.browser)
        self.contentenv = ContentEnvironment(self.browser)
        self.content_views = ContentViews(self.browser)
        self.content_search = ContentSearch(self.browser)
        self.domain = Domain(self.browser)
        self.discoveryrules = DiscoveryRules(self.browser)
        self.environment = Environment(self.browser)
        self.gpgkey = GPGKey(self.browser)
        self.hardwaremodel = HardwareModel(self.browser)
        self.hostgroup = Hostgroup(self.browser)
        self.hosts = Hosts(self.browser)
        self.ldapauthsource = LdapAuthSource(self.browser)
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
        self.rhai = RHAI(self.browser)
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
        a directory same as that of the test method name.

        """
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
        cls.num_buckets = conf.properties['performance.csv.num_buckets']
        cls.vm_list = []
        cls.org_id = cls._get_organization_id()  # get organization-id
        cls.sub_id = ''
        cls.num_iterations = 0     # depend on # of threads or clients
        cls.bucket_size = 0        # depend on # of iterations on each thread

        cls._convert_to_numbers()  # read in string type, convert to numbers
        cls._get_vm_list()         # read in list of virtual machines

        # read default organization from constant module
        cls.default_org = DEFAULT_ORG

    @classmethod
    def _convert_to_numbers(cls):
        """read in string type series, convert to numbers"""
        cls.num_threads = [int(x) for x in cls.num_threads.split(',')]
        cls.num_buckets = int(cls.num_buckets)

    @classmethod
    def _get_vm_list(cls):
        """read in a list of virtual machines ip address"""
        vm_list_string = conf.properties[
            'performance.test.virtual_machines_list']
        cls.vm_list = vm_list_string.split(',')

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
        cls.savepoint = conf.properties.get(savepoint_name, '')
        cls.raw_file_name = raw_file_name
        cls.stat_file_name = stat_file_name

        if raw_reg is not None and stat_reg is not None:
            cls.reg_raw_file_name = raw_reg
            cls.reg_stat_file_name = stat_reg

    @classmethod
    def _get_organization_id(cls):
        """Get organization id"""
        result = OrgCli.list(per_page=False)
        if result.return_code != 0:
            cls.logger.error('Fail to get organization id.')
            raise RuntimeError('Invalid organization id. Stop!')
        return result.stdout[0]['id']

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
        self.logger.info('Reset db from /home/backup/{}'.format(savepoint))
        ssh.command('./reset-db.sh /home/backup/{}'.format(savepoint))

    def _get_subscription_id(self):
        """Get subscription id"""
        result = Subscription.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        if result.return_code != 0:
            self.logger.error('Fail to get subscription id!')
            raise RuntimeError('Invalid subscription id. Stop!')
        subscription_id = result.stdout[0]['id']
        subscription_name = result.stdout[0]['name']
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
            'Timing result is: {}'.format(time_result_dict))

        with open(raw_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # for each thread, write its head and data
            for i in range(current_num_threads):
                writer.writerow(time_result_dict.get('thread-{}'.format(i)))
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
            time_list = time_result_dict.get('thread-{}'.format(i))
            thread_name = 'client-{}'.format(i)
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
                time_list = time_result_dict.get('thread-{}'.format(j))
                # slice out bucket-size from each client's result and merge
                chunks_bucket_i += time_list[
                    i * self.bucket_size: (i + 1) * self.bucket_size
                ]

            # for each chunk i, compute and output its stat
            return_stat = generate_stat_for_concurrent_thread(
                'bucket-{}'.format(i),
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
            time_list = time_result_dict.get('thread-{}'.format(i))
            thread_name = 'client-{}'.format(i)

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
            time_list = time_result_dict.get('thread-{}'.format(i))
            full_list += time_list

        stat_dict = generate_stat_for_concurrent_thread(
            'test-{}'.format(len(time_result_dict)),
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
            thread_name = 'thread-{}'.format(i)
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
            'raw-ak-{}-clients'.format(current_num_threads)
        )

        # write stat result of ak and generate charts
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_ak,
            current_num_threads,
            'stat-ak-{}-clients'.format(current_num_threads)
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
            thread_name = 'thread-{}'.format(i)
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
            'raw-reg-{}-clients'.format(current_num_threads)
        )

        # write raw result of attach
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict_attach,
            current_num_threads,
            'raw-att-{}-clients'.format(current_num_threads)
        )

        # write stat result of register and generate charts
        self._write_stat_csv_chart(
            self.reg_stat_file_name,
            time_result_dict_register,
            current_num_threads,
            'stat-reg-{}-clients'.format(current_num_threads)
        )

        # write stat result of attach and generate charts
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_attach,
            current_num_threads,
            'stat-att-{}-clients'.format(current_num_threads)
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
            time_result_dict_del['thread-{}'.format(i)] = []
            thread = DeleteThread(
                i,
                'thread-{}'.format(i),
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
            'raw-del-{}-clients'.format(current_num_threads)
        )

        # write stat result of del
        self._write_stat_csv_chart(
            self.stat_file_name,
            time_result_dict_del,
            current_num_threads,
            'stat-del-{}-clients'.format(current_num_threads)
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
            'Concurrent Synchronize by {} threads'
            .format(current_num_threads)
        )
        # determine the target repositories' names by configuration
        # sync only a sublist of target repos for each test case
        repo_names_list = self.repo_names_list[:current_num_threads]
        self.logger.debug(
            'Targeting repositories to sync: {}'
            .format(repo_names_list)
        )

        # Create a list to store all threads
        thread_list = []
        # Create a dictionary to store all timing results from each thread
        time_result_dict = {}
        for thread_id in range(current_num_threads):
            time_result_dict['thread-{}'.format(thread_id)] = []

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
                    "thread-{}".format(tid),
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
