# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Subnet CLI
"""

from ddt import data
from ddt import ddt
from robottelo.cli.subnet import Subnet
from robottelo.common.helpers import generate_ipaddr
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import sleep_for_seconds
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSubnet(BaseCLI):
    """
    Subnet CLI tests.
    """

    @classmethod
    def setUpClass(cls):
        BaseCLI.setUpClass()
        cls.subnet_192_168_100 = "subnet-192168100"
        Subnet().delete({'name': cls.subnet_192_168_100})
        Subnet().create_minimal(cls.subnet_192_168_100)

    @attr('cli', 'subnet')
    def test_create(self):
        """ `subnet create` basic test (minimal params required) """
        result = Subnet().create_minimal()
        self.assertTrue(result.return_code == 0,
                        "Subnet create - exit code %d" %
                        result.return_code)

    @attr('cli', 'subnet')
    def test_info(self):
        """`subnet info` basic test """
        options = {}
        options['name'] = generate_name(8, 8)
        options['network'] = generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'

        Subnet().create(options)
        sleep_for_seconds(5)

        result = Subnet().info({'name': options['name']})

        self.assertTrue(len(result.stdout) > 1,
                          "Subnet info - returns 1 record")
        self.assertEquals(result.stdout['Name'], options['name'],
                          "Subnet info - check name")

    @attr('cli', 'subnet')
    def test_list(self):
        """ `subnet list` basic test """
        result = Subnet().list({'per-page': '10'})
        self.assertGreater(len(result.stdout), 0,
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
        self.assertTrue(result.return_code == 0,
                        "Subnet update - exit code %d" %
                        result.return_code)

    @attr('cli', 'subnet')
    def test_delete(self):
        """ `subnet delete` basic test """
        name = generate_name()
        options = {}
        options['name'] = name
        result = Subnet().create_minimal(name)
        self.assertTrue(result.return_code == 0,
                        "Subnet create - exit code %d" %
                        result.return_code)
        result = Subnet().delete(options)
        self.assertTrue(result.return_code == 0,
                        "Subnet delete - exit code %d" %
                        result.return_code)
