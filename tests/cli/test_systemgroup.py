# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization CLI
"""

from robottelo.cli.factory import make_systemgroup
from tests.cli.basecli import BaseCLI
from robottelo.cli.systemgroup import Systemgroup


class TestSystemgroup(BaseCLI):
    """
    Tests for Systemgroups via Hammer CLI
    """

    def __assert_exists(self, args):
        """
        Checks if the object that passed as args parameter really exists
        in `hammer user list --search args['login']` and has values of:
        Login,Name,Email
        """
        result = Systemgroup.list({'search': 'name=\"%s\"' % args['name']})
        self.assertTrue(result.return_code == 0,
                        "Systemgroup search - exit code %d" %
                        result.return_code)
        self.assertTrue(result.stdout[0]['name'] == args['name'],
                        "Systemgroup search - check our value 'Name'")

    def test_crud_create_nolimit(self):
        """
        @test: Create systemgroup with no max limit.
        @feature: Systemgroup
        @assert: Systemgroup is created.
        """

        new_obj = make_systemgroup({'organization-id': 'ACME_Corporation'})
        # Can we find the new object?
        self.__assert_exists(new_obj)
