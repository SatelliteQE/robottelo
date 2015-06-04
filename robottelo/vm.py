"""Utilities to create clients

Clients are virtual machines provisioned on a ``provisioning_server``. All
virtual machine images are stored on the ``image_dir`` path on the provisioning
server.

Make sure to configure the ``clients`` section on the configuration file. Also
make sure that the server have in place: the base images for rhel66 and rhel71,
snap-guest and its dependencies and the ``image_dir`` path created.

"""
import logging
import os
import time

from robottelo.common import conf, ssh


BASE_IMAGES = ('rhel71', 'rhel70', 'rhel66', 'rhel65')

logger = logging.getLogger(__name__)


class VirtualMachineError(Exception):
    """Exception raised for failed virtual machine management operations"""


class VirtualMachine(object):
    """Manages a virtual machine to allow client provisioning for robottelo

    It expects that base images listed on ``BASE_IMAGES`` are created and
    snap-guest is setup on the provisioning server.

    This also can be used as a context manager::

        with VirtualMachine() as vm:
            result = vm.run('ls')
            out = result.stdout

    Make sure to call :meth:`destroy` to stop and clean the image on the
    provisioning server, otherwise the virtual machine and its image will stay
    on the server consuming hardware resources.

    It is possible to customize the ``provisioning_server`` and ``image_dir``
    as per virtual machine basis. Just set the wanted values when
    instantiating.

    """

    def __init__(
            self, cpu=1, ram=512, distro=None, provisioning_server=None,
            image_dir=None):
        self.cpu = cpu
        self.ram = ram
        if distro is None or distro not in BASE_IMAGES:
            self.distro = BASE_IMAGES[0]
        else:
            self.distro = distro
        if provisioning_server is None:
            self.provisioning_server = conf.properties.get(
                'clients.provisioning_server')
        else:
            self.provisioning_server = provisioning_server
        if image_dir is None:
            self.image_dir = conf.properties.get(
                'clients.image_dir', '/var/lib/libvirt/images/')
        else:
            self.image_dir = image_dir

        self.target_image = str(id(self))
        self.ip_addr = None
        self.hostname = None
        self._created = False

    def create(self):
        """Creates a virtual machine on the provisioning server using
        snap-guest

        :raises robottelo.vm.VirtualMachineError: Whenever a virtual machine
            could not be executed.

        """
        if self._created:
            return

        if self.provisioning_server is None:
            raise VirtualMachineError('Provisioning server is not configured')

        command_args = [
            'snap-guest',
            '-b {source_image}',
            '-t {target_image}',
            '-m {vm_ram}',
            '-c {vm_cpu}',
            '-n bridge=br0 -f',
        ]

        if self.image_dir is not None:
            command_args.append('-p {image_dir}')

        command = ' '.join(command_args).format(
            source_image='{0}-base'.format(self.distro),
            target_image=self.target_image,
            vm_ram=self.ram,
            vm_cpu=self.cpu,
            image_dir=self.image_dir,
        )

        result = ssh.command(command, self.provisioning_server)

        if result.return_code != 0:
            raise VirtualMachineError(
                u'Failed to run snap-guest: {0}'.format(result.stderr))

        # Give some time to machine boot
        time.sleep(60)

        result = ssh.command(
            'ping -c 1 {}.local'.format(self.target_image),
            self.provisioning_server
        )
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to fetch virtual machine IP address information')
        output = ''.join(result.stdout)
        self.ip_addr = output.split('(')[1].split(')')[0]
        self._created = True

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        if not self._created:
            return

        result = ssh.command(
            'virsh destroy {0}'.format(self.target_image),
            hostname=self.provisioning_server
        )
        if result.return_code > 0:
            logger.warning(result.stderr)
        result = ssh.command(
            'virsh undefine {0}'.format(self.target_image),
            hostname=self.provisioning_server
        )
        if result.return_code > 0:
            logger.warning(result.stderr)

        image_name = '{0}.img'.format(self.target_image)
        result = ssh.command(
            'rm {0}'.format(os.path.join(self.image_dir, image_name)),
            hostname=self.provisioning_server
        )
        if result.return_code > 0:
            logger.warning(result.stderr)

    def download_install_rpm(self, repo_url, package_name):
        """Downloads and installs custom rpm on the virtual machine.

        :param repo_url: URL to repository, where package is located.
        :param package_name: Desired package name.
        :return: None.
        :raises robottelo.vm.VirtualMachineError: If package wasn't installed.

        """
        self.run(
            'wget -nd -r -l1 --no-parent -A \'{0}.rpm\' {1}'
            .format(package_name, repo_url)
        )
        self.run('rpm -i {0}.rpm'.format(package_name))
        result = self.run('rpm -q {0}'.format(package_name))
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to install {0} rpm.'.format(package_name)
            )

    def enable_repo(self, repo):
        """Enables specified Red Hat repository on the virtual machine.

        :param repo: Red Hat repository name.
        :return: None.

        """
        self.run('subscription-manager repos --enable {0}'.format(repo))

    def install_katello_agent(self):
        """Installs katello agent on the virtual machine.

        :return: None.
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't
            installed.

        """
        self.run('yum install -y katello-agent')
        result = self.run('rpm -q katello-agent')
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install katello-agent')

    def install_katello_cert(self):
        """Downloads and installs katello-ca rpm on the virtual machine.

        :return: None.
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't
            installed.

        """
        self.run(
            'wget -nd -r -l1 --no-parent -A \'*.noarch.rpm\' http://{0}/pub/'
            .format(conf.properties['main.server.hostname'])
        )
        self.run('rpm -i katello-ca-consumer*.noarch.rpm')
        result = self.run(
            'rpm -q katello-ca-consumer-{0}'
            .format(conf.properties['main.server.hostname'])
        )
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install katello-ca rpm')

    def register_contenthost(self, activation_key, org):
        """Registers content host on foreman server using activation-key.

        :param activation_key: Activation key name to register content host
            with.
        :param org: Organization name to register content host for.
        :return: None.

        """
        self.run(
            'subscription-manager register --activationkey {0} '
            '--org {1} --force'
            .format(activation_key, org)
        )

    def run(self, cmd):
        """Runs a ssh command on the virtual machine

        :param str cmd: Command to run on the virtual machine
        :return: A :class:`robottelo.common.ssh.SSHCommandResult` instance with
            the commands results
        :rtype: robottelo.common.ssh.SSHCommandResult
        :raises robottelo.vm.VirtualMachineError: If the virtual machine is not
            created.

        """
        if not self._created:
            raise VirtualMachineError(
                'The virtual machine should be created before running any ssh '
                'command'
            )

        return ssh.command(cmd, hostname=self.ip_addr)

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, *exc):
        self.destroy()
