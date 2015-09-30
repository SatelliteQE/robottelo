# -*- encoding: utf-8 -*-
"""Test class for Global parameters CLI"""

from fauxfactory import gen_string
from robottelo.cli.globalparam import GlobalParameter
from robottelo.decorators import run_only_on
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestGlobalParameter(CLITestCase):
    """GlobalParameter related CLI tests."""

    def test_set(self):
        """@Test: Check if Global Param can be set

        @Feature: Global Param - Set

        @Assert: Global Param is set

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })

    def test_list(self):
        """@Test: Test Global Param List

        @Feature: Global Param - List

        @Assert: Global Param List is displayed

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], value)

    def test_delete(self):
        """@Test: Check if Global Param can be deleted

        @Feature: Global Param - Delete

        @Assert: Global Param is deleted

        """
        name = 'opt-%s' % gen_string('alpha', 10)
        value = 'val-%s %s' % (
            gen_string('alpha', 10), gen_string('alpha', 10))
        GlobalParameter().set({
            'name': name,
            'value': value,
        })
        GlobalParameter().delete({'name': name})
        result = GlobalParameter().list({'search': name})
        self.assertEqual(len(result), 0)
