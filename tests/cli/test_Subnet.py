#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data
from ddt import ddt
from lib.common.helpers import generate_ipaddr
from lib.common.helpers import generate_name
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSubnet(BaseCLI):
    """
    Subnet related tests.
    """

    def _init_once(self):
        """
        a method invoked only once and setup some self.__class__.<properties>
        """
        self.__class__.subnet_update_ok_name = generate_name(8, 8)
        self.__class__.subnet_update_ok_network = generate_ipaddr(ip3=True)

        self.subnet.create_minimal(self.subnet_update_ok_name,
            self.subnet_update_ok_network)  # needs for update DDT tests.

    @attr('cli', 'subnet')
    def test_create(self):
        """
        create basic operation of subnet with minimal parameters required.
        """

        self.assertTrue(self.subnet.create_minimal(),
                        'Subnet created - no error')

    @attr('cli', 'subnet')
    def test_info(self):
        """
        basic `info` operation test.
        TODO - FOR DEMO ONLY, NEEDS TO BE REWORKED [gkhachik].
        """

        options = {}
        options['name'] = generate_name(8, 8)
        options['network'] = generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'

        self.subnet.create(options)

        _ret = self.subnet.info({'name': options['name']})

        self.assertEquals(len(_ret), 1,
                          "Subnet info - returns 1 record")
        self.assertEquals(_ret[0]['Name'], options['name'],
                          "Subnet info - check name")

    @attr('cli', 'subnet')
    def test_list(self):
        """
        basic `list` operation test.
        TODO - FOR DEMO ONLY, NEEDS TO BE REWORKED [gkhachik].
        """

        _ret = self.subnet.list({'per-page': '10'})
        self.assertGreater(len(_ret), 0,
                           "Subnet list - returns > 0 records")

    @data(
          {'network': generate_ipaddr(ip3=True)},
          {'mask': '255.255.0.0'},
          {'gateway': '192.168.101.54'},
          {'dns-primary': '192.168.100.0'},
          {'dns-secondary': '10.17.100.0'},
          {'network': '192.168.100.0', 'from': '192.168.100.1',
           'to': '192.168.100.255'},
          {'vlanid': '1'},
          )
    @attr('cli', 'subnet')
    def test_update_success_ddt(self, option_dict):
        options = {}
        options['name'] = self.subnet_update_ok_name
        for option in option_dict:
            options[option] = option_dict[option]
        self.assertTrue(self.subnet.update(options), "Subnet update - true")
