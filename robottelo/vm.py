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

from robottelo import ssh
from robottelo.config import conf
from robottelo.helpers import get_server_cert_rpm_url

BASE_IMAGES = (
    'rhel65',
    'rhel66',
    'rhel67',
    'rhel70',
    'rhel71',
)

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
            image_dir=None, tag=None):
        self.cpu = cpu
        self.ram = ram
        self.distro = BASE_IMAGES[-1] if distro is None else distro
        if self.distro not in BASE_IMAGES:
            raise VirtualMachineError(
                u'{0} is not a supported distro. Choose one of {1}'
                .format(self.distro, ', '.join(BASE_IMAGES))
            )
        if provisioning_server is None:
            self.provisioning_server = conf.properties.get(
                'clients.provisioning_server')
        else:
            self.provisioning_server = provisioning_server
        if self.provisioning_server is None or self.provisioning_server == '':
            raise VirtualMachineError(
                'A provisioning server must be provided. Make sure to fill '
                '"provisioning_server" on clients section of your robottelo '
                'configuration. Or provide a not None provisioning_server '
                'argument.'
            )
        if image_dir is None:
            self.image_dir = conf.properties.get(
                'clients.image_dir', '/var/lib/libvirt/images/')
        else:
            self.image_dir = image_dir

        self.hostname = None
        self.ip_addr = None
        self._domain = None
        self._created = False
        self._subscribed = False
        self._target_image = str(id(self))
        if tag is not None:
            self._target_image = tag + self._target_image

    def create(self):
        """Creates a virtual machine on the provisioning server using
        snap-guest

        :raises robottelo.vm.VirtualMachineError: Whenever a virtual machine
            could not be executed.

        """
        if self._created:
            return

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

        if self._domain is None:
            try:
                self._domain = self.provisioning_server.split('.', 1)[1]
            except IndexError:
                raise VirtualMachineError(
                    u"Failed to fetch domain from provisioning server: {0} "
                    .format(self.provisioning_server))

        command = u' '.join(command_args).format(
            source_image=u'{0}-base'.format(self.distro),
            target_image=u'{0}.{1}'.format(self._target_image, self._domain),
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
            u'ping -c 1 {0}.local'.format(self._target_image),
            self.provisioning_server
        )
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to fetch virtual machine IP address information')
        output = ''.join(result.stdout)
        self.ip_addr = output.split('(')[1].split(')')[0]
        self.hostname = u'{0}.{1}'.format(self._target_image, self._domain)
        self._created = True

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        if not self._created:
            return
        if self._subscribed:
            self.unregister()

        ssh.command(
            u'virsh destroy {0}'.format(self.hostname),
            hostname=self.provisioning_server
        )
        ssh.command(
            u'virsh undefine {0}'.format(self.hostname),
            hostname=self.provisioning_server
        )
        image_name = u'{0}.img'.format(self.hostname)
        ssh.command(
            u'rm {0}'.format(os.path.join(self.image_dir, image_name)),
            hostname=self.provisioning_server
        )

    def download_install_rpm(self, repo_url, package_name):
        """Downloads and installs custom rpm on the virtual machine.

        :param repo_url: URL to repository, where package is located.
        :param package_name: Desired package name.
        :return: None.
        :raises robottelo.vm.VirtualMachineError: If package wasn't installed.

        """
        self.run(
            u'wget -nd -r -l1 --no-parent -A \'{0}.rpm\' {1}'
            .format(package_name, repo_url)
        )
        self.run(u'rpm -i {0}.rpm'.format(package_name))
        result = self.run(u'rpm -q {0}'.format(package_name))
        if result.return_code != 0:
            raise VirtualMachineError(
                u'Failed to install {0} rpm.'.format(package_name)
            )

    def enable_repo(self, repo):
        """Enables specified Red Hat repository on the virtual machine.

        :param repo: Red Hat repository name.
        :return: None.

        """
        self.run(u'subscription-manager repos --enable {0}'.format(repo))

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
        result = self.run(
            u'rpm -Uvh {0}'.format(get_server_cert_rpm_url())
        )
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to download and install the katello-ca rpm')
        result = self.run(
            u'rpm -q katello-ca-consumer-{0}'
            .format(conf.properties['main.server.hostname'])
        )
        if result.return_code != 0:
            raise VirtualMachineError('Failed to find the katello-ca rpm')

    def register_contenthost(self, activation_key, org, releasever=None):
        """Registers content host on foreman server using activation-key.

        :param activation_key: Activation key name to register content host
            with.
        :param org: Organization name to register content host for.
        :return: SSHCommandResult instance filled with the result of the
            registration.

        """
        cmd = (
            u'subscription-manager register --activationkey {0} --org {1}'
            .format(activation_key, org)
        )
        if releasever is not None:
            cmd += u' --release {0}'.format(releasever)
        cmd = cmd + u' --force'
        result = self.run(cmd)
        if result.return_code == 0:
            self._subscribed = True
        return result

    def unregister(self):
        """Run subscription-manager unregister.

        :return: SSHCommandResult instance filled with the result of the
            unregistration.

        """
        return self.run(u'subscription-manager unregister')

    def run(self, cmd):
        """Runs a ssh command on the virtual machine

        :param str cmd: Command to run on the virtual machine
        :return: A :class:`robottelo.ssh.SSHCommandResult` instance with
            the commands results
        :rtype: robottelo.ssh.SSHCommandResult
        :raises robottelo.vm.VirtualMachineError: If the virtual machine is not
            created.

        """
        if not self._created:
            raise VirtualMachineError(
                'The virtual machine should be created before running any ssh '
                'command'
            )

        return ssh.command(cmd, hostname=self.ip_addr)

    def get(self, remote_path, local_path=None):
        """Get a remote file from the virtual machine."""
        if not self._created:
            raise VirtualMachineError(
                'The virtual machine should be created before getting any file'
            )
        ssh.download_file(remote_path, local_path, hostname=self.ip_addr)

    def put(self, local_path, remote_path=None):
        """Put a local file to the virtual machine."""
        if not self._created:
            raise VirtualMachineError(
                'The virtual machine should be created before putting any file'
            )
        ssh.upload_file(local_path, remote_path, hostname=self.ip_addr)

    def configure_rhel_repo(self, rhel_repo):
        """Configures specified Red Hat repository on the virtual machine.

        :param rhel_repo: Red Hat repository link from properties file.
        :return: None.

        """
        # 'Access Insights', 'puppet' requires RHEL 6/7 repo and it is not
        # possible to sync the repo during the tests as they are huge(in GB's)
        # hence this adds a file in /etc/yum.repos.d/rhel6/7.repo
        self.run(
            'wget -O /etc/yum.repos.d/rhel.repo {0}'
            .format(rhel_repo)
        )

    def configure_puppet(self, rhel_repo=None):
        """Configures puppet on the virtual machine/Host.

        :param rhel_repo: Red Hat repository link from properties file.
        :return: None.

        """
        sat6_hostname = conf.properties['main.server.hostname']
        self.configure_rhel_repo(rhel_repo)
        puppet_conf = (
            'pluginsync      = true\n'
            'report          = true\n'
            'ignoreschedules = true\n'
            'daemon          = false\n'
            'ca_server       = {0}\n'
            'server          = {1}\n'
            .format(sat6_hostname, sat6_hostname)
        )
        result = self.run(u'yum install puppet -y')
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to install the puppet rpm')
        self.run(
            'echo "{0}" >> /etc/puppet/puppet.conf'
            .format(puppet_conf)
        )
        # This particular puppet run on client would populate a cert on sat6
        # under the capsule --> certifcates or via cli "puppet cert list", so
        # that we sign it.
        self.run(u'puppet agent -t')
        ssh.command(u'puppet cert sign --all')
        # This particular puppet run would create the host entity under
        # 'All Hosts' and let's redirect stderr to /dev/null as errors at this
        # stage can be ignored.
        self.run(u'puppet agent -t 2> /dev/null')

    def execute_foreman_scap_client(self, policy_id=None):
        """Executes foreman_scap_client on the vm/clients to create security
        audit report.

        :param policy_id: The Id of the OSCAP policy.
        :return: None.

        """
        if policy_id is None:
            result = self.run(
                u'awk -F "/" \'/download_path/ {print $4}\' '
                '/etc/foreman_scap_client/config.yaml'
            )
            policy_id = result.stdout[0]
        self.run(u'foreman_scap_client {0}'.format(policy_id))
        if result.return_code != 0:
            raise VirtualMachineError(
                'Failed to execute foreman_scap_client run.')

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, *exc):
        self.destroy()
