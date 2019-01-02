"""Tests for :mod:`robottelo.vm`."""
import unittest2
from robottelo import ssh
from robottelo.config.base import DistroSettings
from robottelo.vm import VirtualMachine, VirtualMachineError

from unittest.mock import call, patch


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

    def configure_provisoning_server(self):
        """Helper for configuring the provisioning server on robottelo config.

        """
        self.settings.clients.provisioning_server = self.provisioning_server

    @patch('time.sleep')
    @patch('robottelo.ssh.command', side_effect=[
        ssh.SSHCommandResult(),
        ssh.SSHCommandResult(stdout=['(192.168.0.1)']),
        ssh.SSHCommandResult()
    ])
    def test_dont_create_if_already_created(
            self, ssh_command, sleep):
        """Check if the creation steps are run more than once"""
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
        self.assertEqual(ssh_command.call_count, 3)

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
        ssh_command.assert_called_once_with(
            'ls', hostname='192.168.0.1', timeout=None)

    def test_name_limit(self):
        """Check whether exception is risen in case of too long host name (more
        than 59 chars)"""
        self.configure_provisoning_server()
        domain = self.provisioning_server.split('.', 1)[1]
        with self.assertRaises(VirtualMachineError):
            VirtualMachine(
                tag='test',
                target_image='a'*(59 - len(domain))
            )

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
