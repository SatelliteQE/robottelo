#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""
Usage:
    hammer global_parameter [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set                           Set a global parameter.
    list                          List all common parameters.
    delete                        Delete a common_parameter
"""
from lib.cli.globalparam import GlobalParameter
from lib.common.helpers import generate_name, sleep_for_seconds
from tests.cli.basecli import BaseCLI


class TestGlobalParameter(BaseCLI):
    """ GlobalParameter related CLI tests. """

    def test_set(self):
        """ `global_parameter set` basic test """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
        result = GlobalParameter().set({
                                        'name': name,
                                        'value': value
                                        })
        self.assertEquals(result['retcode'], 0,
                          "GlobalParameter set - exit code %d" %
                          result['retcode'])

    def test_list(self):
        """ `global_parameter list` basic test """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
        result = GlobalParameter().set({
                                        'name': name,
                                        'value': value
                                        })
        self.assertEquals(result['retcode'], 0,
                          "GlobalParameter set - exit code %d" %
                          result['retcode'])
        result = GlobalParameter().list({'search': name})
        self.assertEquals(result['retcode'], 0,
                          "GlobalParameter list - exit code %d" %
                          result['retcode'])
        self.assertEquals(len(result['stdout']), 1,
                          "GlobalParameter list - stdout has one record")
        self.assertEquals(result['stdout'][0]['Value'], value,
                          "GlobalParameter list - value matches")

    def test_delete(self):
        """ `global_parameter delete` basic test """
        name = "opt-%s" % generate_name(8, 8)
        value = "val-%s" % generate_name(12, 12) + " " + generate_name()
        result = GlobalParameter().set({
                                        'name': name,
                                        'value': value
                                        })
        self.assertEquals(result['retcode'], 0,
                          "GlobalParameter set - exit code %d" %
                          result['retcode'])
        result = GlobalParameter().delete({'name': name})
        self.assertEquals(result['retcode'], 0,
                          "GlobalParameter delete - exit code %d" %
                          result['retcode'])
        sleep_for_seconds(5)
        result = GlobalParameter().list({'search': name})
        self.assertNotEquals(result['retcode'], 0,
                          "GlobalParameter list - exit code is not 0 but %d" %
                          result['retcode'])
