"""Test class for concurrent subscription by register and attach"""
from robottelo.performance.constants import (
    ATTACH_ENV,
    RAW_ATT_FILE_NAME,
    RAW_REG_FILE_NAME,
    STAT_ATT_FILE_NAME,
    STAT_REG_FILE_NAME,
)
from robottelo.test import ConcurrentTestCase


class ConcurrentSubAttachTestCase(ConcurrentTestCase):
    """Concurrent Subscribe to Red Hat Satellite 6 Server by attach tests"""

    @classmethod
    def setUpClass(cls):
        super(ConcurrentSubAttachTestCase, cls).setUpClass()

        # parameters for concurrent register and attach test
        # note: may need to change savepoint name
        cls._set_testcase_parameters(
            'enabled_repos',
            RAW_ATT_FILE_NAME,
            STAT_ATT_FILE_NAME,
            raw_reg=RAW_REG_FILE_NAME,
            stat_reg=STAT_REG_FILE_NAME,
        )

        # parameters for attach step
        cls.environment = ATTACH_ENV

    def setUp(self):
        super(ConcurrentSubAttachTestCase, self).setUp()

        # Get subscription id
        (self.sub_id, sub_name) = self._get_subscription_id()
        self.logger.debug(
            'subscription {0} id is: {1}'.format(sub_name, self.sub_id))

    def test_subscribe_ak_sequential(self):
        """Subscribe system sequentially using 1 virtual machine

        @Steps:

        1. create result dictionary
        2. sequentially run by one thread;
           the thread iterates all total number of iterations
        3. produce result of timing

        @Assert: Restoring where there's no system registered

        """
        self.kick_off_ak_test(self.num_threads[0], 5000)

    def test_register_attach_2_clients(self):
        """Subscribe system concurrently using 2 virtual machines

        @Steps:

        1. create result dictionary
        2. concurrent run by multiple threads;
           each thread iterates a limited number of times
        3. produce result of timing

        @Assert: Restoring from database without any registered systems.

        """
        self.kick_off_att_test(self.num_threads[1], 5000)

    def test_register_attach_4_clients(self):
        """Subscribe system concurrently using 4 virtual machines

        @Assert: Restoring from database without any registered systems.

        """
        self.kick_off_att_test(self.num_threads[2], 5000)

    def test_register_attach_6_clients(self):
        """Subscribe system concurrently using 6 virtual machines

        @Assert: Restoring from database without any registered systems.

        """
        self.kick_off_att_test(self.num_threads[3], 6000)

    def test_register_attach_8_clients(self):
        """Subscribe system concurrently using 8 virtual machines

        @Assert: Restoring from database without any registered systems.

        """
        self.kick_off_att_test(self.num_threads[4], 5000)

    def test_register_attach_10_clients(self):
        """Subscribe system concurrently using 10 virtual machines

        @Steps:

        1. create result dictionary
        2. concurrent run by multiple threads;
           and each thread iterates a limited number of times
        3. produce result of timing

        @Assert: Restoring from database without any registered systems.

        """
        self.kick_off_att_test(self.num_threads[5], 5000)
