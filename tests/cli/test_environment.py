# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment  CLI
"""

from robottelo.cli.environment import Environment
from robottelo.common.helpers import generate_name, sleep_for_seconds
from tests.cli.basecli import BaseCLI


class TestEnvironment(BaseCLI):

    def test_create(self):
        result = Environment().create({'name': generate_name()})
        self.assertTrue(result.return_code == 0,
                        "Environment create - retcode")

    def test_info(self):
        name = generate_name()
        Environment().create({'name': name})
        sleep_for_seconds(5)  # give time to appear in the list
        result = Environment().info({'name': name})
        self.assertEquals(
            len(result.stdout), 1, "Environment info - return count"
        )
        self.assertEquals(result.stdout[0]['Name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        name = generate_name()
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - stdout contains 'Name'")

    def test_update(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        result = Environment().update({'name': name,
                                      'new-name': "updated_%s" % name})
        self.assertTrue(result.return_code == 0,
                        "Environment update - retcode")
        result = Environment().list({'search': "updated_%s" % name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - has updated name")

    def test_delete(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        result = Environment().delete({'name': name})
        self.assertTrue(result.return_code == 0,
                        "Environment delete - retcode")
        sleep_for_seconds(5)  # sleep for about 5 sec.
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 0,
                        "Environment list - does not have deleted name")
