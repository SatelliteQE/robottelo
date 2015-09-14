"""Tests for :mod:`robottelo.vm`."""
import unittest2

from mock import call, patch
from robottelo import ssh
from robottelo.config import conf
from robottelo.vm import VirtualMachine, VirtualMachineError


class VirtualMachineTestCase(unittest2.TestCase):
    """Tests for :class:`robottelo.vm.VirtualMachine`."""

    provisioning_server = 'provisioning.example.com'

    def setUp(self):
        super(VirtualMachineTestCase, self).setUp()
        self.properties_backup = conf.properties.copy()
        conf.properties['clients.provisioning_server'] = None

    def tearDown(self):
        super(VirtualMachineTestCase, self).tearDown()
        conf.properties = self.properties_backup

    def configure_provisoning_server(self):
        """Helper for configuring the provisioning server on robottelo config.

        """
        key = 'clients.provisioning_server'
        conf.properties[key] = self.provisioning_server

    @patch('time.sleep')
    @patch('robottelo.ssh.command', side_effect=[
        ssh.SSHCommandResult(),
        ssh.SSHCommandResult(stdout=['(192.168.0.1)']),
    ])
    def test_dont_create_if_already_created(
            self, ssh_command, sleep):
        """Check if the creation steps does run more than one"""
        self.configure_provisoning_server()
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
        self.configure_provisoning_server()
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
        self.configure_provisoning_server()
        vm = VirtualMachine()
        with self.assertRaises(VirtualMachineError):
            vm.run('ls')

    @patch('robottelo.ssh.command')
    def test_destroy(self, ssh_command):
        """Check if destroy runs the required ssh commands"""
        self.configure_provisoning_server()
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
                 hostname=self.provisioning_server),
            call('virsh undefine {0}'.format(vm.hostname),
                 hostname=self.provisioning_server),
            call('rm {0}/{1}.img'.format(image_dir, vm.hostname),
                 hostname=self.provisioning_server),
        ]

        self.assertListEqual(ssh_command.call_args_list, ssh_command_args_list)
