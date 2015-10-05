# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use, invalid-name
"""proxy class for Smart proxy CLI"""

import random

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy, default_url_on_new_port
from robottelo.decorators import run_only_on
from robottelo.helpers import valid_data_list
from robottelo.test import CLITestCase


@run_only_on('sat')
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

    def test_proxy_create(self):
        """@Test: Proxy creation with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is created

        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                self.assertEquals(proxy['name'], name)

    def test_proxy_delete(self):
        """@Test: Proxy deletion with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                Proxy.delete({u'id': proxy['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Proxy.info({u'id': proxy['id']})

    def test_proxy_update(self):
        """@Test: Proxy name update with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy has the name updated

        """
        proxy = make_proxy({u'name': gen_alphanumeric()})
        newport = random.randint(9091, 49090)
        for new_name in valid_data_list():
            with self.subTest(new_name):
                with default_url_on_new_port(9090, newport) as url:
                    Proxy.update({
                        u'id': proxy['id'],
                        u'name': new_name,
                        u'url': url,
                    })
                    proxy = Proxy.info({u'id': proxy['id']})
                    self.assertEqual(proxy['name'], new_name)

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
