#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer subnet [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a subnet
    info                          Show a subnet.
    list                          List of subnets
    update                        Update a subnet
    delete                        Delete a subnet
"""
from ddt import data
from ddt import ddt
from lib.cli.subnet import Subnet
from lib.common.helpers import generate_ipaddr
from lib.common.helpers import generate_name
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSubnet(BaseCLI):
    """
    Subnet CLI tests.
    """
    subnet_192_168_100 = "subnet-192168100"

    def _init_once(self):
        """ a method invoked only once """
        #  needs for update DDT tests.
        Subnet().delete({'name': self.subnet_192_168_100})
        Subnet().create_minimal(self.subnet_192_168_100)

    @attr('cli', 'subnet')
    def test_create(self):
        """ `subnet create` basic test (minimal params required) """
        result = Subnet().create_minimal()
        self.assertTrue(result.get_return_code() == 0,
                        "Subnet create - exit code %d" %
                        result.get_return_code())

    @attr('cli', 'subnet')
    def test_info(self):
        """`subnet info` basic test """
        options = {}
        options['name'] = generate_name(8, 8)
        options['network'] = generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'

        Subnet().create(options)

        result = Subnet().info({'name': options['name']})

        self.assertEquals(len(result.get_stdout()), 1,
                          "Subnet info - returns 1 record")
        self.assertEquals(result.get_stdout()[0]['Name'], options['name'],
                          "Subnet info - check name")

    @attr('cli', 'subnet')
    def test_list(self):
        """ `subnet list` basic test """
        result = Subnet().list({'per-page': '10'})
        self.assertGreater(len(result.get_stdout()), 0,
                           "Subnet list - returns > 0 records")

    @data(
        {'network': generate_ipaddr(ip3=True)},
        {'mask': '255.255.0.0'},
        {'gateway': '192.168.101.54'},
        {'dns-primary': '192.168.100.0'},
        {'dns-secondary': '10.17.100.0'},
        {
            'network': '192.168.100.0',
            'from': '192.168.100.1',
            'to': '192.168.100.255',
        },
        {'vlanid': '1'},
    )
    @attr('cli', 'subnet')
    def test_update_success_ddt(self, option_dict):
        """ `subnet update` basic test (different options) """
        options = {}
        options['name'] = self.subnet_192_168_100
        for option in option_dict:
            options[option] = option_dict[option]
        result = Subnet().update(options)
        self.assertTrue(result.get_return_code() == 0,
                        "Subnet update - exit code %d" %
                        result.get_return_code())

    @attr('cli', 'subnet')
    def test_delete(self):
        """ `subnet delete` basic test """
        name = generate_name()
        options = {}
        options['name'] = name
        result = Subnet().create_minimal(name)
        self.assertTrue(result.get_return_code() == 0,
                        "Subnet create - exit code %d" %
                        result.get_return_code())
        result = Subnet().delete(options)
        self.assertTrue(result.get_return_code() == 0,
                        "Subnet delete - exit code %d" %
                        result.get_return_code())
