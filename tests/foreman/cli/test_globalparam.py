# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""
Test class for Global parameters CLI
"""

from robottelo.cli.globalparam import GlobalParameter
from robottelo.common.helpers import generate_name, sleep_for_seconds
from tests.cli.basecli import BaseCLI


class TestGlobalParameter(BaseCLI):
    """ GlobalParameter related CLI tests. """

    def test_set(self):
        """
        @Feature: Global Param - Set
        @Test: Check if Global Param can be set
        @Assert: Global Param is set
        """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
        result = GlobalParameter().set({
            'name': name,
            'value': value})
        self.assertEquals(result.return_code, 0,
                          "GlobalParameter set - exit code %d" %
                          result.return_code)

    def test_list(self):
        """
        @Feature: Global Param - List
        @Test: Test Global Param List
        @Assert: Global Param List is displayed
        """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
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
        """
        @Feature: Global Param - Delete
        @Test: Check if Global Param can be deleted
        @Assert: Global Param is deleted
        """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
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
        sleep_for_seconds(5)
        result = GlobalParameter().list({'search': name})
        self.assertTrue(len(result.stdout) == 0,
                        "GlobalParameter list - deleted item is not listed")
