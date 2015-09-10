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
        name = "opt-%s" % gen_string("alpha", 10)
        val_part1 = gen_string("alpha", 10)
        val_part2 = gen_string("alpha", 10)
        value = "val-%s %s" % (val_part1, val_part2)
        result = GlobalParameter().set({
            'name': name,
            'value': value})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter set - exit code %d" %
                          result.return_code)

    def test_list(self):
        """@Test: Test Global Param List

        @Feature: Global Param - List

        @Assert: Global Param List is displayed

        """
        name = "opt-%s" % gen_string("alpha", 10)
        val_part1 = gen_string("alpha", 10)
        val_part2 = gen_string("alpha", 10)
        value = "val-%s %s" % (val_part1, val_part2)
        result = GlobalParameter().set({
            'name': name,
            'value': value})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter set - exit code %d" %
                          result.return_code)
        result = GlobalParameter().list({'search': name})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter list - exit code %d" %
                          result.return_code)
        self.assertEquals(len(result.stdout), 1,
                          "GlobalParameter list - stdout has one record")
        self.assertEquals(result.stdout[0]['value'], value,
                          "GlobalParameter list - value matches")

    def test_delete(self):
        """@Test: Check if Global Param can be deleted

        @Feature: Global Param - Delete

        @Assert: Global Param is deleted

        """
        name = "opt-%s" % gen_string("alpha", 10)
        val_part1 = gen_string("alpha", 10)
        val_part2 = gen_string("alpha", 10)
        value = "val-%s %s" % (val_part1, val_part2)
        result = GlobalParameter().set({
            'name': name,
            'value': value})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter set - exit code %d" %
                          result.return_code)
        result = GlobalParameter().delete({'name': name})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter delete - exit code %d" %
                          result.return_code)
        result = GlobalParameter().list({'search': name})
        self.assertTrue(len(result.stdout) == 0,
                        "GlobalParameter list - deleted item is not listed")
