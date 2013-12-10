#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

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
    Subnet related tests.
    """
    subnet_192_168_100 = "subnet-192168100"

    def _init_once(self):
        """
        a method invoked only once and setup some self.__class__.<properties>
        """
        # needs for update DDT tests.
        Subnet().delete({'name': self.subnet_192_168_100})
        Subnet().create_minimal(self.subnet_192_168_100)

    @attr('cli', 'subnet')
    def test_create(self):
        """
        create basic operation of subnet with minimal parameters required.
        """

        self.assertTrue(Subnet().create_minimal(),
                        'Subnet created - no error')

    @attr('cli', 'subnet')
    def test_info(self):
        """
        basic `info` operation test.
        """

        options = {}
        options['name'] = generate_name(8, 8)
        options['network'] = generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'

        Subnet().create(options)

        _ret = Subnet().info({'name': options['name']})

        self.assertEquals(len(_ret['stdout']), 1,
                          "Subnet info - returns 1 record")
        self.assertEquals(_ret['stdout'][0]['Name'], options['name'],
                          "Subnet info - check name")

    @attr('cli', 'subnet')
    def test_list(self):
        """
        basic `list` operation test.
        """

        _ret = Subnet().list({'per-page': '10'})
        self.assertGreater(len(_ret['stdout']), 0,
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
        options = {}
        options['name'] = self.subnet_192_168_100
        for option in option_dict:
            options[option] = option_dict[option]
        self.assertTrue(Subnet().update(options), "Subnet update - true")

    @attr('cli', 'subnet')
    def test_delete(self):
        name = generate_name()
        options = {}
        options['name'] = name
        self.assertTrue(Subnet().create_minimal(name))
        self.assertTrue(Subnet().delete(options), "Subnet delete - true")
