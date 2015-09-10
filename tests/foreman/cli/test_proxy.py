# -*- encoding: utf-8 -*-
"""proxy class for Smart proxy CLI"""

import random

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy, default_url_on_new_port
from robottelo.decorators import data, run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestProxy(CLITestCase):

    def setUp(self):  # noqa
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
    def test_proxy_create(self, data):
        """@Test: Proxy creation with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is created

        """
        try:
            proxy = make_proxy({u'name': data['name']})
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEquals(
            proxy['name'],
            data['name'], "Input and output name should be consistent")

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
    )
    def test_proxy_delete(self, data):
        """@Test: Proxy deletion with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is deleted

        """
        try:
            proxy = make_proxy({u'name': data['name']})
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEquals(
            proxy['name'],
            data['name'], "Input and output name should be consistent")

        result = Proxy.delete({u'id': proxy['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Proxy should be deleted"
        )
        self.assertEqual(
            len(result.stderr),
            0,
            "No error excepted"
        )

        result = Proxy.info({u'id': proxy['id']})
        self.assertNotEqual(
            result.return_code,
            0,
            "Proxy should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )

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
    def test_proxy_update(self, data):
        """@Test: Proxy name update with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy has the name updated

        """
        try:
            proxy = make_proxy({u'name': data['name']})
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEquals(
            proxy['name'],
            data['name'], "Input and output name should be consistent")

        with default_url_on_new_port(9090, random.randint(9091, 49090)) as url:
            result = Proxy.update({
                u'id': proxy['id'],
                u'name': data['update'],
                u'url': url})
        self.assertEqual(
            result.return_code,
            0,
            "Proxy should be updated"
        )
        result = Proxy.info({u'id': proxy['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Proxy should be found"
        )
        self.assertEqual(
            result.stdout['name'],
            data['update'],
            "Proxy name should be updated"
        )

    def test_proxy_refresh_features_by_id(self):
        """@Test: Refresh smart proxy features, search for proxy by id

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed

        """
        try:
            proxy = make_proxy()
        except CLIFactoryError as err:
            self.fail(err)
        result = Proxy.refresh_features({u'id': proxy['id']})
        self.assertEqual(result.return_code, 0)

    def test_proxy_refresh_features_by_name(self):
        """@Test: Refresh smart proxy features, search for proxy by name

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed

        """
        try:
            proxy = make_proxy()
        except CLIFactoryError as err:
            self.fail(err)
        result = Proxy.refresh_features({u'name': proxy['name']})
        self.assertEqual(result.return_code, 0)
