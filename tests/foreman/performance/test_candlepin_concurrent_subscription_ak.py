"""Test class for concurrent subscription by Activation Key"""
from datetime import date
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.factory import (make_activation_key)
from robottelo.cli.subscription import Subscription

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
            'performance.csv.raw_ak_file_name',
            'performance.csv.stat_ak_file_name'
        )

        # add date to csv files names
        today = date.today()
        today_str = today.strftime('%Y%m%d')
        cls.raw_file_name = '{0}-{1}'.format(today_str, cls.raw_file_name)
        cls.stat_file_name = '{0}-{1}'.format(today_str, cls.stat_file_name)

    def setUp(self):
        super(ConcurrentSubActivationKeyTestCase, self).setUp()

        # Create activation key
        self.logger.info('Create activation key: ')
        (ak_id, ak_name) = self._create_activation_key()

        # Get subscription id
        self.logger.info('Get subscription id: ')
        (sub_id, sub_name) = self._get_subscription_id()
        self.sub_id = sub_id

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

        # output activation key informatin
        self.logger.info('Retrieve activation keys info list:')
        result = ActivationKey.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        if result.return_code != 0:
            self.logger.error('Fail to make new activation key!')
            return
        self.logger.info(
            'New activation key is: {}.'.format(result.stdout[0]['name']))
        return result.stdout[0]['id'], result.stdout[0]['name']

    def _get_subscription_id(self):
        """Get subscription id"""
        result = Subscription.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        if result.return_code != 0:
            self.logger.error('Fail to get subscription id!')
            return
        subscription_id = result.stdout[0]['id']
        subscription_name = result.stdout[0]['name']
        self.logger.info('Subscribed to {0} with subscription id {1}'
                         .format(subscription_name, subscription_id))
        return subscription_id, subscription_name

    def _add_ak_to_subscription(self, ak_id, sub_id):
        """Add activation key to subscription"""
        result = ActivationKey.add_subscription({
            'id': ak_id,
            'subscription-id': sub_id,
            'quantity': self.add_ak_subscription_qty
        })

        if result.return_code != 0:
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
