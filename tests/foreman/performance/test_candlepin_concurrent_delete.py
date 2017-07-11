"""Test class for concurrent subscription deletion

:Requirement: Candlepin Concurrent Delete

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OTHER

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
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
        """Delete subscriptions using 1 thread

        :id: 19909194-23a4-4ac4-95c0-e8e107cd95b0

        :Steps:

            1. get list of all registered systems' uuid
            2. create result dictionary
            3. create thread names
            4. run by only one thread as deleting sequentially
            5. produce result of timing

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[0])

    def test_delete_2_clients(self):
        """Delete subscriptions concurrently using 2 threads

        :id: 3691eff7-2482-474a-8efb-0e5275a8ca4c

        :Steps:

            1. get list of all registered systems' uuid
            2. create result dictionary
            3. create a list of thread names
            4. concurrent run by multiple threads; each thread delete only a
               sublist of uuids
            5. produce result of timing

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[1])

    def test_delete_4_clients(self):
        """Delete subscriptions concurrently using 4 threads

        :id: 7c68ab12-503d-4aa6-b9fe-0ac44c9a72f2

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[2])

    def test_delete_6_clients(self):
        """Delete subscriptions concurrently using 6 threads

        :id: 7a9dddf3-cc0f-4f27-8f8e-329af6eb85a0

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[3])

    def test_delete_8_clients(self):
        """Delete subscriptions concurrently using 8 threads

        :id: 7ce2c9d3-2eda-4f71-b360-d5f7219d524f

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[4])

    def test_delete_10_clients(self):
        """Delete subscriptions concurrently using 10 virtual machines

        :id: edd74cec-30e3-435a-b604-42c21963b5a3

        :Steps:

            1. get list of all registered systems' uuid
            2. create result dictionary
            3. create a list of thread names
            4. concurrent run by multiple threads; each thread delete only a
               sublist of uuids
            5. produce result of timing

        :expectedresults: Restoring from database would have 5k registered
            systems.
        """
        self.kick_off_del_test(self.num_threads[5])
