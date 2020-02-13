"""Tests for :mod:`robottelo.vm`."""
from unittest.mock import call
from unittest.mock import patch

import unittest2

from robottelo import ssh
from robottelo.config.base import DistroSettings
from robottelo.vm import VirtualMachine
from robottelo.vm import VirtualMachineError


class VirtualMachineTestCase(unittest2.TestCase):
    """Tests for :class:`robottelo.vm.VirtualMachine`."""

    provisioning_server = 'provisioning.example.com'

    def setUp(self):
        super(VirtualMachineTestCase, self).setUp()
        self.settings_patcher = patch('robottelo.vm.settings', spec=True)
        self.settings = self.settings_patcher.start()
        self.settings.clients.provisioning_server = None
        self.settings.distro = DistroSettings()

    def tearDown(self):
        super(VirtualMachineTestCase, self).tearDown()
        self.settings_patcher.stop()

    def configure_provisioning_server(self):
        """Helper for configuring the provisioning server on robottelo config.

        """
        self.settings.clients.provisioning_server = self.provisioning_server

    @patch('time.sleep')
    @patch('robottelo.ssh.command', side_effect=[
        ssh.SSHCommandResult(
            return_code=0,
            stdout=['CPUs:     1', 'Memory:   512 MB', 'MAC:      52:54:00:f7:bb:a8']
        ),
        ssh.SSHCommandResult(return_code=1, stderr=''),
        ssh.SSHCommandResult(stdout=['(192.168.0.1)']),
        ssh.SSHCommandResult()
    ])
    def test_dont_create_if_already_created(
            self, ssh_command, sleep):
        """Check if the creation steps are run more than once"""
        self.configure_provisioning_server()
        vm = VirtualMachine()

        with patch.multiple(
            vm,
            image_dir='/opt/robottelo/images',
            provisioning_server='provisioning.example.com'
        ):
            vm.create()
            vm.create()
        self.assertEqual(vm.ip_addr, '192.168.0.1')
        self.assertEqual(ssh_command.call_count, 4)

    def test_invalid_distro(self):
        """Check if an exception is raised if an invalid distro is passed"""
        with self.assertRaises(VirtualMachineError):
            vm = VirtualMachine(distro='invalid_distro')  # noqa

    def test_provisioning_server_not_configured(self):
        """Check if an exception is raised if missing provisioning_server"""
        with self.assertRaises(VirtualMachineError):
            vm = VirtualMachine()  # noqa

    @patch('robottelo.ssh.command')
    def test_run(self, ssh_command):
        """Check if run calls ssh.command"""
        self.configure_provisioning_server()
        vm = VirtualMachine()

        def create_mock():
            """A mock for create method to set instance vars to run work"""
            vm._created = True
            vm.ip_addr = '192.168.0.1'

        with patch.object(vm, 'create', side_effect=create_mock):
            vm.create()

        vm.run('ls')
        ssh_command.assert_called_once_with(
            'ls', hostname='192.168.0.1', timeout=None)

    def test_name_limit(self):
        """Check whether exception is risen in case of too long host name (more
        than 59 chars)"""
        self.configure_provisioning_server()
        domain = self.provisioning_server.split('.', 1)[1]
        with self.assertRaises(VirtualMachineError):
            VirtualMachine(
                tag='test',
                target_image='a'*(59 - len(domain))
            )

    def test_run_raises_exception(self):
        """Check if run raises an exception if the vm is not created"""
        self.configure_provisioning_server()
        vm = VirtualMachine()
        with self.assertRaises(VirtualMachineError):
            vm.run('ls')

    @patch('robottelo.ssh.command')
    def test_destroy(self, ssh_command):
        """Check if destroy runs the required ssh commands"""
        self.configure_provisioning_server()
        image_dir = '/opt/robottelo/images'
        vm = VirtualMachine()

        with patch.multiple(
            vm,
            image_dir=image_dir,
            _created=True
        ):
            vm.destroy()

        self.assertEqual(ssh_command.call_count, 3)

        ssh_command_args_list = [
            call('virsh destroy {0}'.format(vm.hostname),
                 hostname=self.provisioning_server,
                 connection_timeout=30),
            call('virsh undefine {0}'.format(vm.hostname),
                 hostname=self.provisioning_server,
                 connection_timeout=30),
            call('rm {0}/{1}.img'.format(image_dir, vm.hostname),
                 hostname=self.provisioning_server,
                 connection_timeout=30),
        ]

        self.assertListEqual(ssh_command.call_args_list, ssh_command_args_list)

    @patch('time.sleep')
    @patch('robottelo.ssh.command', side_effect=[
        ssh.SSHCommandResult(
            return_code=0,
            stdout=['CPUs:     1', 'Memory:   512 MB', 'MAC:      52:54:00:f7:bb:a8']
        ),
        ssh.SSHCommandResult(stdout=[
            '{"return":[{"name":"lo","ip-addresses":[{"ip-address-type":"ipv4",'
            '"ip-address":"127.0.0.1","prefix":8}],"hardware-address":"00:00:00:00:00:00"}'
            ',{"name":"ens3","ip-addresses":[{"ip-address-type":"ipv4",'
            '"ip-address":"10.8.30.135","prefix":19}],"hardware-address":"52:54:00:f7:bb:a8"}]}'
        ]),
        ssh.SSHCommandResult()
    ])
    def test_qemu_ga_gets_ip(self, ssh_command, sleep):
        """Verify that the IP is correctly parsed from the qemu-guest-agent output"""
        self.configure_provisioning_server()
        vm = VirtualMachine()
        vm.create()
        self.assertEqual(vm.ip_addr, '10.8.30.135')
