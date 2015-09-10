"""Test class for concurrent subscription deletion"""
from robottelo import ssh
from robottelo.performance.constants import (
    RAW_DEL_FILE_NAME,
    STAT_DEL_FILE_NAME,
)
from robottelo.test import ConcurrentTestCase


class ConcurrentDeleteTestCase(ConcurrentTestCase):
    """Concurrent Deleting subscriptions tests"""

    @classmethod
    def setUpClass(cls):
        super(ConcurrentDeleteTestCase, cls).setUpClass()
        # parameters for concurrent activation key test
        # note: may need to change savepoint name
        cls._set_testcase_parameters(
            'performance.test.savepoint3_after_registered',
            RAW_DEL_FILE_NAME,
            STAT_DEL_FILE_NAME
        )

    def setUp(self):
        super(ConcurrentDeleteTestCase, self).setUp()

    def _get_registered_uuids(self):
        """Get all registered systems' uuids from Postgres"""
        self.logger.info('Get UUID from database:')

        result = ssh.command(
            """su postgres -c 'psql -A -t -d foreman -c """
            """"SELECT uuid FROM katello_systems;"'""")

        if result.return_code != 0:
            self.logger.error('Fail to fetch uuids.')
            raise RuntimeError('Invalid uuids. Stop!')
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
