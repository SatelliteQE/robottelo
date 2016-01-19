"""Test class for concurrent Synchronization"""


import csv

from robottelo.config import settings
from robottelo.performance.constants import (
    RAW_SYNC_FILE_NAME,
    STAT_SYNC_FILE_NAME
)
from robottelo.performance.graph import (
    generate_line_chart_raw_pulp,
    generate_line_chart_stat_pulp,
)
from robottelo.performance.pulp import Pulp
from robottelo.performance.stat import generate_stat_for_pulp_sync
from robottelo.test import ConcurrentTestCase


class ConcurrentSyncTestCase(ConcurrentTestCase):
    """Concurrent Sync with Red Hat CDN

    Initial-Sync test would restore database between each
    iteration, inside a test case. For example, the script
    would sync 2 repos concurrently and, once the longest
    sync completes, it immediately restores to clean all
    cached data. The process is repeated X times and return
    timing values for each thread/repository. Then it would
    continue test case of 3, 4, ..., N repositories by the
    above process.

    Resync test, on the other hand, would not restore db
    between each iteration of a test case. However, it'd
    still restore and sync all target repos sequentially
    once, prior to the test case starts. For 2-repo test
    case, both are synced for first time. Then it starts
    the resync by waiting the longest to finish, and
    immediately going to next iteration without reset
    (also repeated X times in this test case). It still
    restores and syncs for first time before 3, 4, ..., N
    test case starts.

    """
    @classmethod
    def setUpClass(cls):
        super(ConcurrentSyncTestCase, cls).setUpClass()

        # note: may need to change savepoint in config file
        cls._set_testcase_parameters(
            'enabled_repos',
            RAW_SYNC_FILE_NAME,
            STAT_SYNC_FILE_NAME,
        )

        # get enabled repositories information
        cls.map_repo_name_id = Pulp.get_enabled_repos(cls.org_id)
        cls.logger.debug(cls.map_repo_name_id)

        # get number of iterations of syncs that each thread would do
        cls.sync_iterations = settings.performance.sync_count

        # get whether start initial sync or resync test
        sync_parameter = settings.performance.sync_type
        cls.is_initial_sync = True if sync_parameter == 'sync' else False

    def setUp(self):
        super(ConcurrentSyncTestCase, self).setUp()

        # determine all targeting repositories to be synced
        self.repo_names_list = settings.performance.repos
        self.logger.debug(
            'Target Repositories to be synced: {0}'
            .format(self.repo_names_list)
        )

        self.max_num_tests = len(self.repo_names_list)
        self.logger.debug(
            'Max number of repositories to sync: {0}'
            .format(self.max_num_tests)
        )

    def test_concurrent_synchronization(self):
        """
        Synchronize two repos concurrently

        @Steps:

        1. get list of all enabled repositories (setUpClass)
        2. sync 2, 3, ..., X repositories as consecutive test cases
        3. for each test case, delegate synchronization to
            ``robottelo.tests.kick_off_sync_test``
        4. in each test case, get the max timing value on each iteration
            and store into max-timing-dict. For example, for 2-repo
            test case, it sync 2 repositories and repeat 3 three times
                     1       2       3
            repo-1   21.48   13.87   33.16
            repo-2   95.33   81.77   21.69

            Then it would extract the max only and return the dictionary:
            ``{2: [95.33, 81.77, 33.16]}``. Repeat from 2-repo test case
            to 10-repo case.

        """
        total_max_timing = {}
        for current_num_threads in range(2, self.max_num_tests + 1):
            # kick off N-repo sync test case
            self.logger.debug(
                'Kick off {0}-repo test case:'.format(current_num_threads)
            )
            total_max_timing[current_num_threads] = []

            # if resync test, sequentially sync all repos for first time
            if not self.is_initial_sync:
                self.logger.debug(
                    'Initial sync prior to {0}-repo Resync test case:'
                    .format(current_num_threads)
                )
                Pulp.repositories_sequential_sync(
                    self.repo_names_list,
                    self.map_repo_name_id,
                    1
                )
                self.logger.debug(
                    'Initial sync prior to {0}-repo Resync test finished.'
                    .format(current_num_threads)
                )

            subtest_dict = self.kick_off_concurrent_sync_test(
                current_num_threads,
                self.is_initial_sync
            )

            # generate csv and charts for raw data of Pulp tests
            self._write_raw_csv_chart_pulp(
                self.raw_file_name,
                subtest_dict,
                current_num_threads,
                'raw-sync-{0}-clients'.format(current_num_threads)
            )

            # get max for each iteration
            for iteration in range(self.sync_iterations):
                total_max_timing[current_num_threads].append(max([
                    subtest_dict.get('thread-{0}'.format(thread))[iteration]
                    for thread in range(current_num_threads)
                ]))

        self.logger.debug(
            'Total Results for all tests from 2 threads to 10 threads: {0}'
            .format(total_max_timing)
        )
        self._write_stat_pulp_concurrent(total_max_timing)

    def _write_raw_csv_chart_pulp(
            self,
            raw_file_name,
            time_result_dict,
            current_num_threads,
            test_case_name):
        """Write csv and chart for raw data of Pulp Test sync/resync"""
        self.logger.debug(
            'Timing result is: {0}'.format(time_result_dict)
        )

        with open(raw_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow([test_case_name])

            # for each thread, write its head and data
            for i in range(len(time_result_dict)):
                writer.writerow(time_result_dict.get('thread-{0}'.format(i)))
            writer.writerow([])

        # generate line chart of raw data
        test_category = self._get_output_filename(raw_file_name)
        generate_line_chart_raw_pulp(
            time_result_dict,
            'Pulp Synchronization Raw Timings Line Chart - '
            '({0}-{1}-clients)'
            .format(test_category, current_num_threads),
            '{0}-{1}-clients-raw-data-line-chart.svg'
            .format(test_category, current_num_threads)
        )

    def _write_stat_pulp_concurrent(self, total_max_timing):
        """Compute statistics on concurrent sync data across tests"""

        with open(self.stat_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow(['concurrent-sync-stat'])
            writer.writerow(['test-case', 'min', 'median', 'max', 'std'])

        stat_dict = {}
        for test in range(2, len(total_max_timing) + 2):
            time_list = total_max_timing.get(test)
            stat_tuple = generate_stat_for_pulp_sync(
                test,
                time_list,
                self.stat_file_name,
            )
            # insert each returned tuple of statistics into stat_dict
            stat_dict.update({test: stat_tuple})

        generate_line_chart_stat_pulp(
            stat_dict,
            'Satellite 6 Pulp Concurrent Sync Test',
            'perf-statistics-concurrent-sync.svg',
            self.max_num_tests
        )

    def test_sequential_synchronization(self):
        """
        Synchronize two repos sequentially

        @Steps:

        1. get list of all enabled repositories (setUpClass)
        2. Synchronize from the first to last repo sequentially
        3. produce result of timing, delegated to
            ``robottelo.tests.kick_off_sync_test``

        @Assert: Target repositories are enabled

        """
        time_result_dict_sync = Pulp.repositories_sequential_sync(
            self.repo_names_list,
            self.map_repo_name_id,
            self.sync_iterations,
            self.savepoint
        )
        self._write_raw_csv_chart_pulp(
            self.raw_file_name,
            time_result_dict_sync,
            1,
            'raw-sync-sequential'
        )
        self._write_stat_pulp_linear(time_result_dict_sync)

    def _write_stat_pulp_linear(self, time_result_dict):
        """Compute statistics on sequential sync data"""
        with open(self.stat_file_name, 'a') as handler:
            writer = csv.writer(handler)
            writer.writerow(['sequential-sync-stat'])
            writer.writerow(['iteration', 'min', 'median', 'max', 'std'])

        stat_dict = {}
        for i in range(len(time_result_dict)):
            time_list = time_result_dict.get('thread-{0}'.format(i))
            stat_tuple = generate_stat_for_pulp_sync(
                i,
                time_list,
                self.stat_file_name
            )
            stat_dict.update({i: stat_tuple})

        generate_line_chart_stat_pulp(
            stat_dict,
            'Satellite 6 Pulp Sequential Sync Test',
            'perf-statistics-sequential-sync.svg',
            len(self.repo_names_list)
        )
