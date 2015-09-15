"""Test class for concurrent subscription by Activation Key"""
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (make_activation_key)
from robottelo.performance.constants import (
    ACTIVATION_KEY,
    CONTENT_VIEW,
    LIFE_CYCLE_ENV,
    QUANTITY,
    RAW_AK_FILE_NAME,
    STAT_AK_FILE_NAME,
)
from robottelo.test import ConcurrentTestCase


class ConcurrentSubActivationKeyTestCase(ConcurrentTestCase):
    """Concurrently Subscribe to Satellite Server by activation-key tests"""

    @classmethod
    def setUpClass(cls):
        super(ConcurrentSubActivationKeyTestCase, cls).setUpClass()

        # parameters for concurrent activation key test only
        # note: may need to change savepoint name
        cls._set_testcase_parameters(
            'performance.test.savepoint2_enabled_repos',
            RAW_AK_FILE_NAME,
            STAT_AK_FILE_NAME
        )

        # parameters for creating activation key
        cls.ak_name = ACTIVATION_KEY
        cls.content_view = CONTENT_VIEW
        cls.life_cycle_env = LIFE_CYCLE_ENV

        # parameters for adding ak to subscription
        cls.add_ak_subscription_qty = QUANTITY

    def setUp(self):
        super(ConcurrentSubActivationKeyTestCase, self).setUp()

        # Create activation key
        self.logger.info('Create activation key: ')
        (ak_id, ak_name) = self._create_activation_key()
        self.logger.info(
            'New activation key is: {0}; its id is: {1}.'
            .format(ak_name, ak_id)
        )

        # Get subscription id
        (sub_id, sub_name) = self._get_subscription_id()
        self.logger.debug(
            'subscription {0} id is: {1}'.format(sub_name, self.sub_id))

        # Add activation key to subscription
        self._add_ak_to_subscription(ak_id, sub_id)

    def _create_activation_key(self):
        """Create a new activation key named ak-1"""
        make_activation_key({
            'organization-id': self.org_id,
            'content-view': self.content_view,
            'lifecycle-environment': self.life_cycle_env,
            'name': self.ak_name
        })

        # output activation key information
        self.logger.info('Retrieve activation keys info list:')
        try:
            result = ActivationKey.list(
                {'organization-id': self.org_id},
                per_page=False
            )
        except CLIReturnCodeError:
            self.logger.error('Fail to make new activation key!')
            return
        return result[0]['id'], result[0]['name']

    def _add_ak_to_subscription(self, ak_id, sub_id):
        """Add activation key to subscription"""
        try:
            ActivationKey.add_subscription({
                'id': ak_id,
                'quantity': self.add_ak_subscription_qty,
                'subscription-id': sub_id,
            })
        except CLIReturnCodeError:
            self.logger.error('Fail to add activation-key to subscription')
            return
        self.logger.info('Subscription added to this activation key.')

    def test_subscribe_ak_sequential(self):
        """@Test: Subscribe system sequentially using 1 virtual machine

        @Steps:

        1. create activation key (setup)
        2. get subscription id (setup)
        3. add activation key to subscription (setup)
        4. create result dictionary
        5. sequentially run by one thread;
           the thread iterates all total number of iterations
        6. produce result of timing

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[0], 5000)

    def test_subscribe_ak_2_clients(self):
        """@Test: Subscribe system concurrently using 2 virtual machines

        @Steps:

        1. create activation key (setup)
        2. get subscription id (setup)
        3. add activation key to subscription (setup)
        4. create result dictionary
        5. concurrent run by multiple threads;
           each thread iterates a limited number of times
        6. produce result of timing

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[1], 5000)

    def test_subscribe_ak_4_clients(self):
        """@Test: Subscribe system concurrently using 4 virtual machines

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[2], 5000)

    def test_subscribe_ak_6_clients(self):
        """@Test: Subscribe system concurrently using 6 virtual machines

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[3], 6000)

    def test_subscribe_ak_8_clients(self):
        """@Test: Subscribe system concurrently using 8 virtual machines

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[4], 5000)

    def test_subscribe_ak_10_clients(self):
        """@Test: Subscribe system concurrently using 10 virtual machines

        @Steps:

        1. create activation key (setup)
        2. get subscription id (setup)
        3. add activation key to subscription (setup)
        4. create result dictionary
        5. concurrent run by multiple threads
           each thread iterates a limited number of times
        6. produce result of timing

        @Assert: Restoring where there's no activation key or registration

        """
        self.kick_off_ak_test(self.num_threads[5], 5000)
