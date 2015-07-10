"""Test class for concurrent subscription deletion"""
from datetime import date
from robottelo.common import ssh

from robottelo.test import ConcurrentTestCase


class ConcurrentDeleteTestCase(ConcurrentTestCase):
    """Concurrent Deleting subscriptions tests"""

    @classmethod
    def setUpClass(cls):
        super(ConcurrentDeleteTestCase, cls).setUpClass()
        # parameters for concurrent activation key test
        # note: may need to change savepoint name
        cls._set_testcase_parameters(
            'performance.test.savepoint2_enabled_repos',
            'performance.csv.raw_del_file_name',
            'performance.csv.stat_del_file_name'
        )

        # add date to csv files names
        today = date.today()
        today_str = today.strftime('%Y%m%d')
        cls.raw_file_name = '{0}-{1}'.format(today_str, cls.raw_file_name)
        cls.stat_file_name = '{0}-{1}'.format(today_str, cls.stat_file_name)

    def setUp(self):
        super(ConcurrentTestCase, self).setUp()

    def _get_registered_uuids(self):
        """Get all registered systems' uuids from Postgres"""
        self.logger.info('Get UUID from database:')

        result = ssh.command(
            """su postgres -c 'psql -A -t -d candlepin -c """
            """"SELECT uuid FROM cp_consumer;"'""")

        if result.return_code != 0:
            self.logger.error('Fail to fetch uuids.')
            return None
        return result.stdout

    def test_delete_sequential(self):
        """@Test: Delete subscriptions using 1 thread

        @Steps:

        1. get list of all registered systems' uuid
        2. create result dictionary
        3. create thread names
        4. run by only one thread as deleting sequentially
        5. produce result of timing

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[0])

    def test_delete_2_clients(self):
        """@Test: Delete subscriptions concurrently using 2 threads

        @Steps:

        1. get list of all registered systems' uuid
        2. create result dictionary
        3. create a list of thread names
        4. concurrent run by multiple threads;
           each thread delete only a sublist of uuids
        5. produce result of timing

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[1])

    def test_delete_4_clients(self):
        """@Test: Delete subscriptions concurrently using 4 threads

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[2])

    def test_delete_6_clients(self):
        """@Test: Delete subscriptions concurrently using 6 threads

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[3])

    def test_delete_8_clients(self):
        """@Test: Delete subscriptions concurrently using 8 threads

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[4])

    def test_delete_10_clients(self):
        """@Test: Delete subscriptions concurrently using 10 virtual machines

        @Steps:

        1. get list of all registered systems' uuid
        2. create result dictionary
        3. create a list of thread names
        4. concurrent run by multiple threads;
           each thread delete only a sublist of uuids
        5. produce result of timing

        @Assert: Restoring from database would have 5k registered systems.

        """
        self.kick_off_del_test(self.num_threads[5])
