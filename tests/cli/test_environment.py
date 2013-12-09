#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create an environment.
    info                          Show an environment.
    list                          List all environments.
    update                        Update an environment.
    sc_params                     List all smart class parameters
    delete                        Delete an environment.
"""
from lib.cli.environment import Environment
from lib.common.helpers import generate_name, sleep_for_seconds
from tests.cli.basecli import BaseCLI


class TestEnvironment(BaseCLI):

    def test_create(self):
        __ret = Environment().create({'name': generate_name()})
        self.assertTrue(__ret['retcode'] == 0,
                        "Environment create - retcode")

    def test_info(self):
        name = generate_name()
        Environment().create({'name': name})
        sleep_for_seconds(5)  # give time to appear in the list
        __ret = Environment().info({'name': name})
        self.assertEquals(
            len(__ret['stdout']), 1, "Environment info - return count"
        )
        self.assertEquals(__ret['stdout'][0]['Name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        name = generate_name()
        Environment().create({'name': name})
        __ret = Environment().list({'search': name})
        self.assertTrue(len(__ret['stdout']) == 1,
                        "Environment list - stdout contains 'Name'")

    def test_update(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        __ret = Environment().update({'name': name,
                                      'new-name': "updated_%s" % name})
        self.assertTrue(__ret['retcode'] == 0,
                        "Environment update - retcode")
        __ret = Environment().list({'search': "updated_%s" % name})
        self.assertTrue(len(__ret['stdout']) == 1,
                        "Environment list - has updated name")

    def test_delete(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        __ret = Environment().delete({'name': name})
        self.assertTrue(__ret['retcode'] == 0,
                        "Environment delete - retcode")
        sleep_for_seconds(5)  # sleep for about 5 sec.
        __ret = Environment().list({'search': name})
        self.assertTrue(len(__ret['stdout']) == 0,
                        "Environment list - does not have deleted name")
