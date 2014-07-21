# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Smart proxy CLI
"""

from ddt import ddt
from robottelo.cli.factory import make_proxy
from robottelo.cli.proxy import Proxy
from robottelo.common.decorators import data, skip_if_rm_bug_open
from robottelo.common.helpers import generate_string
from robottelo.test import CLITestCase
from robottelo.common import conf


def valid_default_url():
    return "https://%s:9090/" % conf.properties['main.server.hostname']


@ddt
class TestProxy(CLITestCase):

    @skip_if_rm_bug_open('3875')
    def test_redmine_3875(self):
        """
        @Test: Proxy creation with random URL
        @Feature: Smart Proxy
        @Assert: Proxy is not created
        """

        # Create a random proxy
        with self.assertRaises(Exception):
            make_proxy()

    @data(
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
    )
    def test_proxy_create(self, data):
        """
        @Test: Proxy creation with the home proxy
        @Feature: Smart Proxy
        @Assert: Proxy is created
        """
        test = make_proxy({'name': data['name'], 'url': valid_default_url()})
        try:
            self.assertEquals(
                test['name'],
                data['name'], "Input and output name should be consistent")
        except Exception as e:
            self.fail(e)

    @data(
        {u'name': generate_string('alpha', 15)},
        {u'name': generate_string('alphanumeric', 15)},
        {u'name': generate_string('numeric', 15)},
        {u'name': generate_string('latin1', 15)},
        {u'name': generate_string('utf8', 15)},
    )
    def test_proxy_delete(self, data):
        """
        @Test: Proxy deletion with the home proxy
        @Feature: Smart Proxy
        @Assert: Proxy is deleted
        """
        test = make_proxy({'name': data['name'], 'url': valid_default_url()})
        try:
            self.assertEquals(
                test['name'],
                data['name'], "Input and output name should be consistent")
        except Exception as e:
            self.fail(e)

        result = Proxy.info({'id': test['id']})
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
        result = Proxy.delete({'id': test['id']})
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

        result = Proxy.info({'id': test['id']})
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
        """
        @Test: Proxy name update with the home proxy
        @Feature: Smart Proxy
        @Assert: Proxy is created
        """
        test = make_proxy({'name': data['name'], 'url': valid_default_url()})
        try:
            self.assertEquals(
                test['name'],
                data['name'], "Input and output name should be consistent")
        except Exception as e:
            self.fail(e)

        result = Proxy.update({
            'id': test['id'],
            'name': data['update'],
            'url': valid_default_url()})
        self.assertEqual(
            result.return_code,
            0,
            "Proxy should be updated"
        )
        result = Proxy.info({'id': test['id']})
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
