# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use, invalid-name
"""proxy class for Smart proxy CLI"""

import random

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy, default_url_on_new_port
from robottelo.decorators import data, run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestProxy(CLITestCase):
    """Proxy cli tests"""

    def setUp(self):
        """Skipping tests until we can create ssh tunnels"""
        self.skipTest('Skipping tests until we can create ssh tunnels')

    def test_redmine_3875(self):
        """@Test: Proxy creation with random URL

        @Feature: Smart Proxy

        @Assert: Proxy is not created

        """
        # Create a random proxy
        with self.assertRaises(CLIFactoryError):
            make_proxy({
                u'url': u'http://{0}:{1}'.format(
                    gen_string('alpha', 6),
                    gen_string('numeric', 4)),
            })

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
    )
    def test_proxy_create(self, test_data):
        """@Test: Proxy creation with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is created

        """
        proxy = make_proxy({u'name': test_data['name']})
        self.assertEquals(proxy['name'], test_data['name'])

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
    )
    def test_proxy_delete(self, test_data):
        """@Test: Proxy deletion with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is deleted

        """
        proxy = make_proxy({u'name': test_data['name']})
        self.assertEquals(proxy['name'], test_data['name'])
        Proxy.delete({u'id': proxy['id']})
        with self.assertRaises(CLIReturnCodeError):
            Proxy.info({u'id': proxy['id']})

    @data(
        {u'name': gen_string('alpha', 15),
         u'update': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15),
         u'update': gen_string('alpha', 15)},
        {u'name': gen_string('numeric', 15),
         u'update': gen_string('alpha', 15)},
        {u'name': gen_string('latin1', 15),
         u'update': gen_string('alpha', 15)},
        {u'name': gen_string('utf8', 15),
         u'update': gen_string('alpha', 15)},
    )
    def test_proxy_update(self, test_data):
        """@Test: Proxy name update with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy has the name updated

        """
        proxy = make_proxy({u'name': test_data['name']})
        self.assertEquals(proxy['name'], test_data['name'])
        with default_url_on_new_port(9090, random.randint(9091, 49090)) as url:
            Proxy.update({
                u'id': proxy['id'],
                u'name': test_data['update'],
                u'url': url,
            })
        proxy = Proxy.info({u'id': proxy['id']})
        self.assertEqual(proxy['name'], test_data['update'])

    def test_refresh_refresh_features_by_id(self):
        """@Test: Refresh smart proxy features, search for proxy by id

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed

        """
        proxy = make_proxy()
        Proxy.refresh_features({u'id': proxy['id']})

    def test_proxy_refresh_features_by_name(self):
        """@Test: Refresh smart proxy features, search for proxy by name

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed

        """
        proxy = make_proxy()
        Proxy.refresh_features({u'name': proxy['name']})
