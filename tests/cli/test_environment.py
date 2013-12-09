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

    #  TODO - move me to a higher level - if approved.
    #  maybe SSHCommandResult class.
    def __contains_in_list(self, prop_value, result):
        """
        Checks if the {'property': value} is in the returned result list.
        @param prop_value dict of {'property': value}
        @param result: Result object from lib.common.helpers.csv_to_dictionary
        """
        for _property in prop_value.keys():
            found = False
            for res in result:
                if res[_property] == prop_value[_property]:
                    found = True
                    break
            if not found:
                return False
        return True

    def test_create(self):
        __ret = Environment().create({'name': generate_name()})
        self.assertTrue(__ret['retcode'] == 0,
            "Environment create - retcode")
        self.assertEquals(__ret['stdout'][0].strip(),
            Environment.OUT_ENV_CREATED,
            "Environment create - stdout")

    def test_info(self):
        name = generate_name()
        Environment().create({'name': name})
        sleep_for_seconds(5)  # give time to appear in the list
        __ret = Environment().info({'name': name})
        self.assertEquals(len(__ret), 1, "Environment info - return count")
        self.assertEquals(__ret[0]['Name'], name,
            "Environment info - stdout contains 'Name'")

    def test_list(self):
        name = generate_name()
        Environment().create({'name': name})
        __ret = Environment().list()
        self.assertTrue(self.__contains_in_list({'Name': name}, __ret),
            "Environment list - stdout contains 'Name'")

    def test_update(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        __ret = Environment().update({'name': name,
            'new-name': "updated_%s" % name})
        self.assertTrue(__ret['retcode'] == 0,
            "Environment update - retcode")
        self.assertEquals(__ret['stdout'][0].strip(),
            Environment.OUT_ENV_UPDATED,
            "Environment update - stdout")
        __ret = Environment().list()
        self.assertTrue(self.__contains_in_list(
            {'Name': "updated_%s" % name}, __ret),
            "Environment list - stdout contains updated 'Name'")

    def test_delete(self):
        name = generate_name(8, 8)
        Environment().create({'name': name})
        __ret = Environment().delete({'name': name})
        self.assertTrue(__ret['retcode'] == 0,
            "Environment delete - retcode")
        self.assertEquals(__ret['stdout'][0].strip(),
            Environment.OUT_ENV_DELETED,
            "Environment delete - stdout")
        sleep_for_seconds(5)  # sleep for about 5 sec.
        __ret = Environment().list()
        self.assertTrue(not self.__contains_in_list(
            {'Name': name}, __ret),
            "Environment list - stdout does not contain 'Name'")
