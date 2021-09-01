"""Utilities to create virtual host on libvirt with and without PXE boot

Hosts are virtual guests provisioned on a external ``libvirt_host``. All
guests images are stored on the ``image_dir`` path on external libvirt
server.

Make sure to configure the ``compute_resources`` section on the configuration
file. Also make sure that the ``vlan_networking`` section is properly
configured.
"""
import os

from fauxfactory import gen_mac

from robottelo import ssh
from robottelo.config import settings


def _gen_mac_for_libvirt():
    # fe:* MAC range is considered reserved in libvirt
    for _ in range(0, 10):
        mac = gen_mac(multicast=False, locally=True)
        if not mac.startswith('fe'):
            return mac
        mac = None
    if not mac:
        raise ValueError('Unable to generate a valid MAC address')


class LibvirtGuestError(Exception):
    """Exception raised for failed virtual guests on external libvirt"""


class LibvirtGuest:
    """Manages a Libvirt guests to allow host discovery and provisioning

    It expects that Libvirt host is defined with image path.
    Make sure to call :meth:`destroy` to stop and clean the image on the
    libvirt server, otherwise the virtual machine and its image will stay
    on the server consuming hardware resources.

    It is possible to customize the ``libvirt_host`` and ``image_dir``
    as per virtual machine basis. Just set the expected values when
    instantiating.
    """

    def __init__(
        self,
        cpu=1,
        ram=1024,
        boot_iso=False,
        extra_nic=False,
        libvirt_server=None,
        image_dir=None,
        mac=None,
        network=None,
        network_type=None,
    ):
        self.cpu = cpu
        self.ram = ram
        if libvirt_server is None:
            self.libvirt_server = settings.libvirt.libvirt_hostname
        else:
            self.libvirt_server = libvirt_server
        if self.libvirt_server is None or self.libvirt_server == '':
            raise LibvirtGuestError(
                'A libvirt server must be provided. Make sure to fill '
                '"libvirt_server" on compute_resources section of your '
                'robottelo configuration. Or provide a not None '
                'libvirt_server argument.'
            )
        if image_dir is None:
            self.image_dir = settings.compute_resources.libvirt_image_dir
        else:
            self.image_dir = image_dir
        if mac is None:
            self.mac = _gen_mac_for_libvirt()
        if network is None:
            if settings.vlan_networking.bridge or settings.vlan_networking.network:
                if settings.vlan_networking.bridge:
                    self.network_type = 'bridge'
                    self.network = settings.vlan_networking.bridge
                else:
                    self.network_type = 'network'
                    self.network = settings.vlan_networking.network
        else:
            self.network_type = network_type
            self.network = network
        if not self.network:
            raise LibvirtGuestError(
                'A network name must be provided. Make sure to fill "bridge" or "network" on '
                'vlan_networking section of your robottelo configuration.'
                'Or provide a not None network and network_type arguments.'
            )
        self.boot_iso = boot_iso
        self.extra_nic = extra_nic
        self.hostname = None
        self.ip_addr = None
        self._domain = None
        self._created = False
        self.guest_name = 'mac{}'.format(self.mac.replace(':', ""))

    def create(self):
        """Creates a virtual machine on the libvirt server using
        virt-install

        :raises robottelo.libvirt_discovery.LibvirtGuestError: Whenever a virtual guest
            could not be executed.
        """
        if self._created:
            return

        command_args = [
            'virt-install',
            '--hvm',
            '--network={vm_nw_type}:{vm_network}',
            '--mac={vm_mac}',
            '--name={vm_name}',
            '--ram={vm_ram}',
            '--vcpus={vm_cpu}',
            '--os-type=linux',
            '--os-variant=rhel7',
            '--disk path={image_name},size=8',
            '--noautoconsole',
            '--graphics spice,listen=0.0.0.0',
        ]

        if not self.boot_iso:
            # Required for PXE-based host discovery
            command_args.append('--boot network')

        else:
            # Required for PXE-less host discovery, where we boot the host
            # with bootable discovery ISO
            self.boot_iso_name = settings.discovery.discovery_iso
            boot_iso_dir = f'{self.image_dir}/{self.boot_iso_name}'
            command_args.append(f'--cdrom={boot_iso_dir}')

        if self.extra_nic:
            nic_mac = _gen_mac_for_libvirt()
            command_args.append('--network={vm_nw_type}:{vm_network}')
            command_args.append(f'--mac={nic_mac}')

        if self._domain is None:
            try:
                self._domain = self.libvirt_server.split('.', 1)[1]
            except IndexError:
                raise LibvirtGuestError(
                    f"Failed to fetch domain from libvirt server: {self.libvirt_server} "
                )

        self.hostname = f'{self.guest_name}.{self._domain}'
        command = ' '.join(command_args).format(
            vm_nw_type=self.network_type,
            vm_network=self.network,
            vm_mac=self.mac,
            vm_name=self.hostname,
            vm_ram=self.ram,
            vm_cpu=self.cpu,
            image_name=f'{self.image_dir}/{self.hostname}.img',
        )

        result = ssh.command(command, self.libvirt_server)

        if result.status != 0:
            raise LibvirtGuestError(f'Failed to run virt-install: {result.stderr}')

        self._created = True

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        if not self._created:
            return

        ssh.command(f'virsh destroy {self.hostname}', hostname=self.libvirt_server)
        ssh.command(f'virsh undefine {self.hostname}', hostname=self.libvirt_server)
        image_name = f'{self.hostname}.img'
        ssh.command(
            f'rm {os.path.join(self.image_dir, image_name)}',
            hostname=self.libvirt_server,
        )

    def attach_nic(self):
        """Add a new NIC to existing host"""
        if not self._created:
            raise LibvirtGuestError('The virtual guest should be created before updating it')
        nic_mac = _gen_mac_for_libvirt()
        command_args = [
            'virsh attach-interface',
            '--domain={vm_name}',
            '--type={vm_nw_type}',
            '--source={vm_network}',
            '--model=virtio',
            '--mac={vm_mac}',
            '--live',
        ]
        command = ' '.join(command_args).format(
            vm_name=self.hostname,
            vm_nw_type=self.network_type,
            vm_network=self.network,
            vm_mac=nic_mac,
        )

        result = ssh.command(command, self.libvirt_server)

        if result.status != 0:
            raise LibvirtGuestError(f'Failed to run virsh attach-interface: {result.stderr}')

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, *exc):
        self.destroy()
