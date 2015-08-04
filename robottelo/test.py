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
from robottelo.cli.metatest import MetaCLITest
from robottelo.cli.org import Org as OrgCli
from robottelo.cli.subscription import Subscription
from robottelo.common.helpers import get_server_url
from robottelo.common import conf, ssh
from robottelo.performance.constants import(
    DEFAULT_ORG,
    NUM_THREADS,
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
from selenium_factory.SeleniumFactory import SeleniumFactory
from selenium import webdriver

from robottelo.performance.stat import generate_stat_for_concurrent_thread
from robottelo.performance.thread import (
    DeleteThread,
    SubscribeAKThread,
    SubscribeAttachThread
)

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
    def _set_testcase_parameters(cls, savepoint_name,
                                 raw_file_name, stat_file_name):
        # note: set savepoint empty to continue test without restore
        cls.savepoint = conf.properties.get(savepoint_name, '')
        cls.raw_file_name = raw_file_name
        cls.stat_file_name = stat_file_name

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

    def _write_raw_csv_file(self, raw_file_name, time_result_dict,
                            current_num_threads, test_case_name):
        """Write raw timing ak/del results to csv file"""
        self.logger.debug(
            'Timing result is: {}'.format(time_result_dict))

        with open(raw_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # for each thread, write its head and data
            for i in range(current_num_threads):
                writer.writerow([
                    'client-{}'.format(i)
                ])
                writer.writerow(time_result_dict.get('thread-{}'.format(i)))
            writer.writerow([])

    def _write_raw_att_csv_file(self, raw_file_name, time_result_dict,
                                current_num_threads, test_case_name):
        """Write raw timing att results to csv file"""
        self.logger.debug("Timing result is: {}".format(time_result_dict))
        with open(raw_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # for each thread, write its head and data
            for i in range(current_num_threads):
                writer.writerow(['client-{}'.format(i)])
                for index in range(3):
                    writer.writerow(
                        time_result_dict.get('thread-{}'.format(i))[index])
                    writer.writerow([])

    def _write_stat_csv_file(self, stat_file_name, time_result_dict,
                             current_num_threads, test_case_name, is_attach):
        """Generate statistical result of concurrent ak/del/att"""
        with open(stat_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # 1) write stat-per-client-bucketized result of ak/del/att
            writer.writerow(['stat-per-client-bucketized'])
            self._write_stat_per_client_bucketized(
                stat_file_name,
                time_result_dict,
                current_num_threads,
                is_attach
            )
            writer.writerow([])

            # 2) write stat-per-test-bucketized result of ak/del/att
            writer.writerow(['stat-per-test-bucketized'])
            self._write_stat_per_test_bucketized(
                stat_file_name,
                time_result_dict,
                is_attach)
            writer.writerow([])

            # 3) write stat-per-client result of ak/del/att
            writer.writerow(['stat-per-client'])
            self._write_stat_per_client(
                stat_file_name,
                time_result_dict,
                current_num_threads,
                is_attach)
            writer.writerow([])

            # 4) write stat-per-test result of ak/del/att
            writer.writerow(['stat-per-test'])
            self._write_stat_per_test(
                stat_file_name,
                time_result_dict,
                is_attach)
            writer.writerow([])

    def _write_stat_per_client_bucketized(
            self, stat_file_name,
            time_result_dict,
            current_num_threads,
            is_attach):
        """Write bucketized stat of per-client results to csv file

        note: each bucket is a split of a client i

        """
        for i in range(current_num_threads):
            if is_attach:
                time_list = time_result_dict.get('thread-{}'.format(i))[2]
            else:
                time_list = time_result_dict.get('thread-{}'.format(i))
            thread_name = 'client-{}'.format(i)
            generate_stat_for_concurrent_thread(
                thread_name,
                time_list,
                stat_file_name,
                self.bucket_size,
                self.num_buckets)

    def _write_stat_per_test_bucketized(
            self, stat_file_name,
            time_result_dict,
            is_attach):
        """Write bucketized stat of per-test to csv file

        note: each bucket of all clients would merge into a chunk;
        generate stat for each such chunk. For example::

            Input: # of clients = 10
            thread-0: [(50 data) | (50 data)|...]
            thread-1: [(50 data) | (50 data)|...]
            ...
            thread-9: [(50 data) | (50 data)|...]
            Output:
            sublist [500 data in all first buckets of each thread]
                    [500]...[500]

        """
        for i in range(self.num_buckets):
            chunks_bucket_i = []
            for j in range(len(time_result_dict)):
                if is_attach:
                    time_list = time_result_dict.get('thread-{}'.format(j))[2]
                else:
                    time_list = time_result_dict.get('thread-{}'.format(j))
                # slice out bucket-size from each client's result and merge
                chunks_bucket_i += time_list[
                    i * self.bucket_size: (i + 1) * self.bucket_size
                ]

            generate_stat_for_concurrent_thread(
                'bucket-{}'.format(i),
                chunks_bucket_i,
                stat_file_name,
                len(chunks_bucket_i), 1)

    def _write_stat_per_client(self, stat_file_name, time_result_dict,
                               current_num_threads, is_attach):
        """Write stat of per-client results to csv file

        note: take the full list of a client i; calculate stat on the list

        """
        for i in range(current_num_threads):
            if is_attach:
                time_list = time_result_dict.get('thread-{}'.format(i))[2]
            else:
                time_list = time_result_dict.get('thread-{}'.format(i))
            thread_name = 'client-{}'.format(i)
            generate_stat_for_concurrent_thread(
                thread_name,
                time_list,
                stat_file_name,
                len(time_list), 1)

    def _write_stat_per_test(self, stat_file_name,
                             time_result_dict, is_attach):
        """Write stat of per-test results to csv file

        note: take the full dictionary of test and calculate overall stat

        """
        full_list = []
        for i in range(len(time_result_dict)):
            if is_attach:
                time_list = time_result_dict.get('thread-{}'.format(i))[2]
            else:
                time_list = time_result_dict.get('thread-{}'.format(i))
            full_list += time_list

        generate_stat_for_concurrent_thread(
            'test-{}'.format(len(time_result_dict)),
            full_list,
            stat_file_name,
            len(full_list), 1)

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
        time_result_dict = {}

        # Create new threads and start each thread mapped with a vm
        for i in range(current_num_threads):
            thread_name = 'thread-{}'.format(i)
            time_result_dict[thread_name] = []
            thread = SubscribeAKThread(
                i, thread_name, time_result_dict,
                self.num_iterations, self.ak_name,
                self.default_org, current_vm_list[i])
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of ak
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict,
            current_num_threads,
            'raw-ak-{}-clients'.format(current_num_threads))

        # write stat result of ak
        self._write_stat_csv_file(
            self.stat_file_name,
            time_result_dict,
            current_num_threads,
            'stat-ak-{}-clients'.format(current_num_threads), False)

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
        # Create a dictionary to store all timing results from each client
        time_result_dict = {}

        # Create new threads and start each thread mapped with a vm
        for i in range(current_num_threads):
            thread_name = 'thread-{}'.format(i)
            time_result_dict[thread_name] = [[], [], []]

            thread = SubscribeAttachThread(
                i, thread_name, time_result_dict,
                self.num_iterations, self.sub_id,
                self.default_org, self.environment,
                current_vm_list[i])
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of att
        self._write_raw_att_csv_file(
            self.raw_file_name,
            time_result_dict,
            current_num_threads,
            'raw-att-{}-clients'.format(current_num_threads))

        # write stat result of att
        self._write_stat_csv_file(
            self.stat_file_name,
            time_result_dict,
            current_num_threads,
            'stat-att-{}-clients'.format(current_num_threads), True)

    def kick_off_del_test(self, current_num_threads):
        """Refactor out concurrent system deletion test case

        :param int current_num_threads: number of threads
        :param int total_iterations: FIXME

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
        time_result_dict = {}

        # Create new threads and start the thread which has sublist of uuids
        for i in range(current_num_threads):
            time_result_dict['thread-{}'.format(i)] = []
            thread = DeleteThread(
                i, 'thread-{}'.format(i),
                uuid_list[
                    self.num_iterations * i:
                    self.num_iterations * (i + 1)
                ],
                time_result_dict
            )
            thread.start()
            thread_list.append(thread)

        # wait all threads in thread list
        self._join_all_threads(thread_list)

        # write raw result of del
        self._write_raw_csv_file(
            self.raw_file_name,
            time_result_dict,
            current_num_threads,
            'raw-del-{}-clients'.format(current_num_threads))

        # write stat result of del
        self._write_stat_csv_file(
            self.stat_file_name,
            time_result_dict,
            current_num_threads,
            'stat-del-{}-clients'.format(current_num_threads), False)
