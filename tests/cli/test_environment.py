# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment  CLI
"""

from robottelo.cli.environment import Environment
from robottelo.common.helpers import generate_name, sleep_for_seconds
from robottelo.cli.factory import make_environment
from tests.cli.basecli import MetaCLI


class TestEnvironment(MetaCLI):

    factory = make_environment
    factory_obj = Environment

    def test_info(self):
        name = generate_name()
        Environment().create({'name': name})
        sleep_for_seconds(5)  # give time to appear in the list
        result = Environment().info({'name': name})

        self.assertTrue(result.return_code == 0,
                        "Environment info - retcode")

        self.assertEquals(result.stdout['name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        name = generate_name()
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - stdout contains 'Name'")
