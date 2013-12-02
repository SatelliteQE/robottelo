# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""
task: https://github.com/omaciel/robottelo/issues/47
task: <more to follow>
"""

from ddt import ddt, data
from lib.cli.infrastructure import Subnet
from lib.common.helpers import generate_ip3, generate_name
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSubnet(BaseCLI):
    """
    Subnet related tests.
    """
    subnet_name_1 = generate_name(8, 8)
    subnet_network_1 = generate_ip3()

    subnet_update_ok_name = generate_name(8, 8)
    subnet_update_ok_network = generate_ip3()

    @attr('cli', 'subnet')  # TODO makes nose to run group of tests
    def test_create_minimal_required_params(self):
        """
        create basic operation of subnet with minimal parameters required.
        """
        Subnet(self.conn).create_minimal(self.subnet_name_1,
            self.subnet_network_1)
        Subnet(self.conn).create_minimal(self.subnet_update_ok_name,
            self.subnet_update_ok_network)

    @attr('cli', 'subnet')
    def test_info(self):
        """
        basic `info` operation test.
        """
        subnet = Subnet(self.conn)
        _ret = subnet.info({'name': self.subnet_name_1})
        self.assertEquals(len(_ret), 1,
            "Subnet info - returns 1 record")
        self.assertEquals(_ret[0]['Name'], self.subnet_name_1,
            "Subnet info - check name")

    @attr('cli', 'subnet')
    def test_list(self):
        """
        basic `list` operation test.
        """
        subnet = Subnet(self.conn)
        _ret = subnet.list({'per-page': '10'})
        self.assertGreater(len(_ret), 0,
            "Subnet list - returns >0 records")

    @attr('cli', 'subnet')
    def test_remove(self):
        """
        basic `delete` operation test.
        """
        subnet = Subnet(self.conn)
        stdout, stderr = subnet.delete({'name': self.subnet_name_1})
        self.assertTrue(len(stderr) == 0,
            "Subnet delete - error stream is empty")
        self.assertEquals(len(stdout), 1,
            "Subnet delete - len(stdout)=1")
        self.assertEquals(stdout[0].strip(), Subnet.OUT_SUBNET_DELETED,
            "Subnet delete - output string")

    @attr('cli', 'subnet')
    @data(('network', generate_ip3()),
          ('mask', '255.255.0.0'))
    def test_update_success(self, opt_val_pair):
        options = {}
        options['name'] = self.subnet_update_ok_name
        options[opt_val_pair[0]] = opt_val_pair[1]
        subnet = Subnet(self.conn)
        subnet.update(options)
