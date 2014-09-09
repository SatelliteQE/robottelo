"""Tests for :mod:`robottelo.vm`."""
import unittest

from mock import call, patch
from robottelo.common import ssh
from robottelo.vm import VirtualMachine, VirtualMachineError


class VirtualMachineTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.vm.VirtualMachine`."""

    @patch('time.sleep')
    @patch('robottelo.common.ssh.command', side_effect=[
        ssh.SSHCommandResult(),
        ssh.SSHCommandResult(stdout=['(192.168.0.1)'])
    ])
    def test_dont_create_if_already_created(
            self, ssh_command, sleep):
        """Check if the creation steps does run more than one"""
        vm = VirtualMachine()

        with patch.multiple(
            vm,
            image_dir='/opt/robottelo/images',
            provisioning_server='provisioning.example.com'
        ):
            vm.create()
            vm.create()

        self.assertEqual(vm.ip_addr, '192.168.0.1')
        self.assertEqual(ssh_command.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    def test_provisioning_server_not_configured(self):
        """Check if an exception is raised if missing provisioning_server"""
        vm = VirtualMachine()
        with patch.object(vm, 'provisioning_server', None):
            with self.assertRaises(VirtualMachineError):
                vm.create()

    @patch('robottelo.common.ssh.command')
    def test_run(self, ssh_command):
        """Check if run calls ssh.command"""
        vm = VirtualMachine()

        def create_mock():
            """A mock for create method to set instance vars to run work"""
            vm._created = True
            vm.ip_addr = '192.168.0.1'

        with patch.object(vm, 'create', side_effect=create_mock):
            vm.create()

        vm.run('ls')
        ssh_command.assert_called_once_with('ls', hostname='192.168.0.1')

    def test_run_raises_exception(self):
        """Check if run raises an exception if the vm is not created"""
        vm = VirtualMachine()
        with self.assertRaises(VirtualMachineError):
            vm.run('ls')

    @patch('robottelo.common.ssh.command')
    def test_destroy(self, ssh_command):
        """Check if destroy runs the required ssh commands"""
        image_dir = '/opt/robottelo/images'
        provisioning_server = 'provisioning.server.com'
        vm = VirtualMachine()

        with patch.multiple(
            vm,
            image_dir=image_dir,
            provisioning_server=provisioning_server,
            _created=True
        ):
            vm.destroy()

        self.assertEqual(ssh_command.call_count, 3)

        ssh_command_args_list = [
            call('virsh destroy {0}'.format(vm.target_image),
                 hostname=provisioning_server),
            call('virsh undefine {0}'.format(vm.target_image),
                 hostname=provisioning_server),
            call('rm {0}/{1}.img'.format(image_dir, vm.target_image),
                 hostname=provisioning_server),
        ]

        self.assertListEqual(ssh_command.call_args_list, ssh_command_args_list)
