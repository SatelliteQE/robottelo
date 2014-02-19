# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment  CLI
"""

from robottelo.cli.environment import Environment
from robottelo.common.helpers import (
    generate_name, generate_string, sleep_for_seconds)
from robottelo.cli.factory import make_environment
from tests.cli.basecli import MetaCLI


class TestEnvironment(MetaCLI):

    factory = make_environment
    factory_obj = Environment

    POSITIVE_CREATE_DATA = (
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10).encode("utf-8")},
        {'name': generate_string("numeric", 10).encode("utf-8")},
    )

    POSITIVE_UPDATE_DATA = (
        ({'name': generate_string("alpha", 10)},
         {'new-name': generate_string("alpha", 10)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("alphanumeric", 10)}),
        ({'name': generate_string("numeric", 10)},
         {'new-name': generate_string("numeric", 10)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'name': generate_string("alphanumeric", 10).encode("utf-8")},
         {'new-name': generate_string("alphanumeric", 300).encode("utf-8")}),
        ({'name': generate_string("alphanumeric", 10).encode("utf-8")},
         {'new-name': generate_string("latin1", 10).encode("utf-8")}),
        ({'name': generate_string("alphanumeric", 10).encode("utf-8")},
         {'new-name': generate_string("utf8", 10).encode("utf-8")}),
        ({'name': generate_string("alphanumeric", 10).encode("utf-8")},
         {'new-name': generate_string("html", 6)}),
        ({'name': generate_string("alphanumeric", 10).encode("utf-8")},
         {'new-name': ""}),
    )

    POSITIVE_DELETE_DATA = (
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10)},
        {'name': generate_string("numeric", 10)},
    )

    def test_info(self):
        """
        @Feature: Environment - Info
        @Test: Test Environment Info
        @Assert: Environment Info is displayed
        """
        name = generate_name()
        Environment().create({'name': name})
        sleep_for_seconds(5)  # give time to appear in the list
        result = Environment().info({'name': name})

        self.assertTrue(result.return_code == 0,
                        "Environment info - retcode")

        self.assertEquals(result.stdout['name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        """
        @Feature: Environment - List
        @Test: Test Environment List
        @Assert: Environment List is displayed
        """
        name = generate_name()
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - stdout contains 'Name'")
