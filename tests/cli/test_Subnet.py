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

    subnet_update_ok_name = generate_name(8, 8)
    subnet_update_ok_network = generate_ipaddr(ip3=True)

    @attr('cli', 'subnet')  # TODO makes nose to run group of tests
    def test_create_minimal_required_params(self):
        """
        create basic operation of subnet with minimal parameters required.
        """

        options = {}
        options['name'] = generate_name(8, 8)
        options['network'] = generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'

        self.assertTrue(self.subnet.create(options), 'Subnet created')

        self.subnet.create_minimal(self.subnet_update_ok_name,
            self.subnet_update_ok_network)

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

    @data(('network', generate_ipaddr(ip3=True)),
          ('mask', '255.255.0.0'))
    @attr('cli', 'subnet')
    def test_update_success_ddt(self, option_and_value):
        options = {}
        options['name'] = self.subnet_update_ok_name
        options[option_and_value[0]] = option_and_value[1]
        self.subnet.update(options)
