"""Tests for :mod:`robottelo.vm`."""
from unittest.mock import call
from unittest.mock import patch

import pytest
from paramiko import SSHException
from paramiko.ssh_exception import NoValidConnectionsError

from robottelo import ssh
from robottelo.config.base import DistroSettings
from robottelo.constants import NO_REPOS_AVAILABLE
from robottelo.constants import SM_OVERALL_STATUS
from robottelo.vm import VirtualMachine
from robottelo.vm import VirtualMachineError


PROV_SERVER_DEFAULT = 'provisioning.example.com'


class TestVirtualMachine:
    """Tests for :class:`robottelo.vm.VirtualMachine`."""

    @pytest.fixture(scope="function")
    def vm_settings_patch(self):
        """Provide mock patches scoped to the function for vm settings"""
        settings_patcher = patch('robottelo.vm.settings', spec=True)
        vm_patch = settings_patcher.start()
        vm_patch.clients.provisioning_server = None
        vm_patch.distro = DistroSettings()

        yield vm_patch
        settings_patcher.stop()

    @pytest.fixture(scope="function")
    def host_os_version_patch(self):
        """Provide mock patches scoped to the function for host_os_version calls"""
        host_patcher = patch('robottelo.vm.get_host_os_version')
        host_patcher.start()
        host_patcher.return_value = 'RHEL7.2.1'

        yield host_patcher
        host_patcher.stop()

    @pytest.fixture(scope="function")
    def config_provisioning_server(self, vm_settings_patch):
        vm_settings_patch.clients.provisioning_server = PROV_SERVER_DEFAULT

    def test_invalid_distro(self):
        """Check if an exception is raised if an invalid distro is passed"""
        with pytest.raises(VirtualMachineError):
            VirtualMachine(distro='invalid_distro')  # noqa

    def test_provisioning_server_not_configured(self):
        """Check if an exception is raised if missing provisioning_server"""
        with pytest.raises(VirtualMachineError, match=r'A provisioning server must be provided.*'):
            VirtualMachine()

    @pytest.mark.parametrize('exception_type', [NoValidConnectionsError, SSHException])
    def test_host_unreachable(self, exception_type):
        """Look for VirtualMachineError if the host is unreachable"""
        with patch('robottelo.ssh.command') as ssh_mock:
            ssh_mock.side_effect = exception_type
        with pytest.raises(VirtualMachineError, match=f'{exception_type.__name__}'):
            VirtualMachine()

    def test_run(self, config_provisioning_server, host_os_version_patch):
        """Check if run calls ssh.command"""
        vm = VirtualMachine()

        def create_mock():
            """A mock for create method to set instance vars to run work"""
            vm._created = True
            vm.ip_addr = '192.168.0.1'

        with patch.object(vm, 'create', side_effect=create_mock):
            vm.create()

        with patch('robottelo.ssh.command') as ssh_mock:
            vm.run('ls')
            ssh_mock.assert_called_once_with('ls', hostname='192.168.0.1', timeout=None)

    def test_name_limit(self, vm_settings_patch, config_provisioning_server):
        """Check whether exception is risen in case of too long host name (more
        than 59 chars)"""
        domain = PROV_SERVER_DEFAULT.split('.', 1)[1]
        with pytest.raises(VirtualMachineError):
            VirtualMachine(tag='test', target_image='a' * (59 - len(domain)))

    def test_run_raises_exception(self, config_provisioning_server, host_os_version_patch):
        """Check if run raises an exception if the vm is not created"""
        vm = VirtualMachine()
        with pytest.raises(VirtualMachineError):
            vm.run('ls')

    @patch('time.sleep')
    @patch(
        'robottelo.ssh.command',
        side_effect=[
            ssh.SSHCommandResult(
                return_code=0,
                stdout=['CPUs:     1', 'Memory:   512 MB', 'MAC:      52:54:00:f7:bb:a8'],
            ),
            ssh.SSHCommandResult(return_code=1, stderr=''),
            ssh.SSHCommandResult(stdout=['(192.168.0.1)']),
            ssh.SSHCommandResult(),
        ],
    )
    def test_dont_create_if_already_created(
        self, ssh__mock, sleep, config_provisioning_server, host_os_version_patch
    ):
        """Check if the creation steps are run more than once"""
        vm = VirtualMachine()

        with patch.multiple(
            vm, image_dir='/opt/robottelo/images', provisioning_server=PROV_SERVER_DEFAULT
        ):
            vm.create()
            vm.create()
        assert vm.ip_addr == '192.168.0.1'
        assert ssh__mock.call_count == 4

    @patch('robottelo.ssh.command')
    def test_destroy(self, ssh_command, config_provisioning_server, host_os_version_patch):
        """Check if destroy runs the required ssh commands"""
        image_dir = '/opt/robottelo/images'
        vm = VirtualMachine()

        with patch.multiple(vm, image_dir=image_dir, _created=True):
            vm.destroy()

        assert ssh_command.call_count == 3

        ssh_command_args_list = [
            call(
                f'virsh destroy {vm.hostname}',
                hostname=PROV_SERVER_DEFAULT,
                connection_timeout=30,
            ),
            call(
                f'virsh undefine {vm.hostname}',
                hostname=PROV_SERVER_DEFAULT,
                connection_timeout=30,
            ),
            call(
                f'rm {image_dir}/{vm.hostname}.img',
                hostname=PROV_SERVER_DEFAULT,
                connection_timeout=30,
            ),
        ]

        assert ssh_command.call_args_list == ssh_command_args_list

    @patch('time.sleep')
    @patch(
        'robottelo.ssh.command',
        side_effect=[
            ssh.SSHCommandResult(
                return_code=0,
                stdout=['CPUs:     1', 'Memory:   512 MB', 'MAC:      52:54:00:f7:bb:a8'],
            ),
            ssh.SSHCommandResult(
                stdout=[
                    '{"return":[{"name":"lo","ip-addresses":[{"ip-address-type":"ipv4",'
                    '"ip-address":"127.0.0.1","prefix":8}],'
                    '"hardware-address":"00:00:00:00:00:00"}'
                    ',{"name":"ens3","ip-addresses":[{"ip-address-type":"ipv4",'
                    '"ip-address":"10.8.30.135","prefix":19}],'
                    '"hardware-address":"52:54:00:f7:bb:a8"}]}'
                ]
            ),
            ssh.SSHCommandResult(),
        ],
    )
    def test_qemu_ga_gets_ip(
        self, ssh_command, sleep, config_provisioning_server, host_os_version_patch
    ):
        """Verify that the IP is correctly parsed from the qemu-guest-agent output"""
        vm = VirtualMachine()
        vm.create()
        assert vm.ip_addr == '10.8.30.135'

    @patch('time.sleep')
    @patch(
        'robottelo.ssh.command',
        side_effect=[
            ssh.SSHCommandResult(
                return_code=0,
                stdout=['CPUs:     1', 'Memory:   512 MB', 'MAC:      52:54:00:f7:bb:a8'],
            ),
            ssh.SSHCommandResult(
                stdout=[
                    '{"return":[{"name":"lo","ip-addresses":[{"ip-address-type":"ipv4",'
                    '"ip-address":"127.0.0.1","prefix":8}],'
                    '"hardware-address":"00:00:00:00:00:00"},'
                    '{"name":"ens3","ip-addresses":[{"ip-address-type":"ipv4",'
                    '"ip-address":"10.8.30.135","prefix":19}],'
                    '"hardware-address":"52:54:00:f7:bb:a8"}]}'
                ]
            ),
            ssh.SSHCommandResult(),
            ssh.SSHCommandResult(stdout=SM_OVERALL_STATUS['current']),
            ssh.SSHCommandResult(stdout=NO_REPOS_AVAILABLE),
        ],
    )
    def test_subscription_manager_overall_status(
        self, ssh_command, sleep, config_provisioning_server, host_os_version_patch
    ):
        vm = VirtualMachine()
        vm.create()
        assert vm.subscription_manager_status().stdout == 'Overall Status: Current'
        assert (
            vm.subscription_manager_list_repos().stdout
            == 'This system has no repositories available through subscriptions.'
        )
