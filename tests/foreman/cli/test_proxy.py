# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""proxy class for Smart proxy CLI"""

from ddt import ddt
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy, default_url_on_new_port
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_string
from robottelo.test import CLITestCase
import random


@ddt
class TestProxy(CLITestCase):

    def setUp(self):
        """Skipping tests until we can create ssh tunnels"""
        self.skipTest('Skipping tests until we can create ssh tunnels')

    @skip_if_bug_open('redmine', 3875)
    def test_redmine_3875(self):
        """@Test: Proxy creation with random URL

        @Feature: Smart Proxy

        @Assert: Proxy is not created

        """

        # Create a random proxy
        with self.assertRaises(Exception):
            make_proxy(
                {u'url': u'http://%s:%s' % (generate_string('alpha', 6),
                                            generate_string('numeric', 4))})

    @data(
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
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
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
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

        result = Proxy.info({u'id': proxy['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Proxy should be found"
        )
        self.assertEqual(
            len(result.stderr),
            0,
            "No error excepted"
        )
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
        {u'name': generate_string('alpha', 15),
         u'update': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15),
         u'update': generate_string('alpha', 15)},
        {u'name': generate_string('numeric', 15),
         u'update': generate_string('alpha', 15)},
        {u'name': generate_string('latin1', 15),
         u'update': generate_string('alpha', 15)},
        {u'name': generate_string('utf8', 15),
         u'update': generate_string('alpha', 15)},
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
