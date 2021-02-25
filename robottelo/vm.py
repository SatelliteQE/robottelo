"""Utilities to create clients

Clients are virtual machines provisioned on a ``provisioning_server``. All
virtual machine images are stored on the ``image_dir`` path on the provisioning
server.

Make sure to configure the ``clients`` section on the configuration file. Also
make sure that the server have in place: the base images for rhel66 and rhel71,
snap-guest and its dependencies and the ``image_dir`` path created.

"""
import json
import logging
import os
import sys
from time import sleep
from urllib.parse import urljoin
from urllib.parse import urlunsplit

from cached_property import cached_property
from fauxfactory import gen_string
from wait_for import wait_for

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.constants import DISTRO_SLES11
from robottelo.constants import DISTRO_SLES12
from robottelo.constants import REPOS
from robottelo.helpers import install_katello_ca
from robottelo.helpers import remove_katello_ca
from robottelo.host_info import get_host_os_version

logger = logging.getLogger('robottelo')


class VirtualMachineError(Exception):
    """Exception raised for failed virtual machine management operations"""


class VirtualMachine:
    """Manages a virtual machine to allow client provisioning for robottelo

    It expects that base images are created and snap-guest is setup on the
    provisioning server.

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
        self,
        cpu=1,
        ram=512,
        distro=None,
        provisioning_server=None,
        image_dir=None,
        tag=None,
        hostname=None,
        domain=None,
        source_image=None,
        target_image=None,
        bridge=None,
        network=None,
    ):
        image_map = {
            DISTRO_RHEL6: settings.distro.image_el6,
            DISTRO_RHEL7: settings.distro.image_el7,
            DISTRO_RHEL8: settings.distro.image_el8,
            DISTRO_SLES11: settings.distro.image_sles11,
            DISTRO_SLES12: settings.distro.image_sles12,
        }
        self.cpu = cpu
        self.mac = None
        self.ram = ram
        self.nw_type = None
        if distro is None:
            # use the same distro as satellite host server os
            from paramiko.ssh_exception import NoValidConnectionsError, SSHException

            try:
                server_host_os_version = get_host_os_version()
            except (NoValidConnectionsError, SSHException):
                import traceback

                trace = sys.exc_info()
                tb_lines = '\n'.join(traceback.format_tb(trace[2]))
                core_exc = trace[1]
                raise VirtualMachineError(
                    'Exception connecting via ssh to get host os version:\n'
                    f'{tb_lines}\n{core_exc}'
                )
            if server_host_os_version.startswith('RHEL6'):
                distro = DISTRO_RHEL6
            elif server_host_os_version.startswith('RHEL7'):
                distro = DISTRO_RHEL7
            else:
                raise VirtualMachineError(
                    'Cannot find a default compatible distro using '
                    f'host OS version: {server_host_os_version}'
                )

        self.distro = distro
        if self.distro not in self.allowed_distros:
            raise VirtualMachineError(
                f'{self.distro} is not a supported distro. Choose one of {self.allowed_distros}'
            )

        self.provisioning_server = provisioning_server or settings.clients.provisioning_server

        if self.provisioning_server in [None, '']:
            raise VirtualMachineError(
                'A provisioning server must be provided. Make sure to fill '
                '"provisioning_server" on clients section of your robottelo '
                'configuration. Or provide a not None provisioning_server '
                'argument.'
            )
        if image_dir is None:
            self.image_dir = settings.clients.image_dir
        else:
            self.image_dir = image_dir

        self._hostname = hostname
        self.ip_addr = None
        self._domain = domain
        self._created = False
        self._subscribed = False
        self._source_image = source_image or '{}-base'.format(image_map.get(self.distro))
        self._target_image = target_image or gen_string('alphanumeric', 16).lower()
        if tag:
            self._target_image = tag + self._target_image
        self.bridge = bridge
        self.network = network
        if len(self.hostname) > 59:
            raise VirtualMachineError(
                'Max virtual machine name is 59 chars (see BZ1289363). Name '
                '"{}" is {} chars long. Please provide shorter name'.format(
                    self.hostname, len(self.hostname)
                )
            )

    @cached_property
    def allowed_distros(self):
        """This is needed in construction, record it for easy reference
        Property instead of a class attribute to delay reading of the settings
        """
        return [DISTRO_RHEL6, DISTRO_RHEL7, DISTRO_RHEL8, DISTRO_SLES11, DISTRO_SLES12]

    @property
    def subscribed(self):
        return self._subscribed

    @property
    def domain(self):
        if self._domain is None:
            try:
                domain = self.provisioning_server.split('.', 1)[1]
            except IndexError:
                raise VirtualMachineError(
                    "Failed to fetch domain from provisioning server: {} ".format(
                        self.provisioning_server
                    )
                )
        else:
            domain = self._domain
        return domain

    @property
    def hostname(self):
        if self._hostname:
            return self._hostname
        else:
            return f'{self._target_image}.{self.domain}'

    @property
    def target_image(self):
        if self._hostname:
            return self._target_image
        else:
            return self.hostname

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
            '-n {nw_type}={nw_name} -f',
            '--qemu-ga',
        ]

        if self.image_dir is not None:
            command_args.append('-p {image_dir}')

        if self._hostname is not None:
            command_args.append('--hostname {hostname}')

        if self._domain is not None:
            command_args.append('-d {domain}')

        if self.bridge is None and self.network is None:
            self.bridge = 'br0'
        if self.bridge is not None:
            self.nw_type = 'bridge'
        if self.network is not None:
            self.nw_type = 'network'

        command = ' '.join(command_args).format(
            source_image=self._source_image,
            target_image=self.target_image,
            vm_ram=self.ram,
            vm_cpu=self.cpu,
            image_dir=self.image_dir,
            hostname=self.hostname,
            domain=self.domain,
            nw_name=self.bridge or self.network,
            nw_type=self.nw_type,
        )

        result = ssh.command(command, self.provisioning_server, connection_timeout=30)
        if result.return_code != 0:
            raise VirtualMachineError(f'Failed to run snap-guest: {result.stderr}')
        else:
            self._created = True
            self.mac = [n.split('MAC:')[1].strip() for n in result.stdout if 'MAC:' in n][0]
        # outside of VLANs ping from hypervisor, in VLANs ping from SAT
        if self.bridge == 'br0':
            ping_from_hostname = self.provisioning_server
        else:
            ping_from_hostname = settings.server.hostname

        # Give some time to machine boot
        for i in range(60):
            qemu_ga_check = ssh.command(
                'virsh qemu-agent-command {0} '
                '\'{{"execute":"guest-network-get-interfaces"}}\''.format(self.hostname),
                ping_from_hostname,
                connection_timeout=30,
            )
            if qemu_ga_check.return_code != 0:
                if 'guest agent is not connected' in qemu_ga_check.stderr:
                    # this means the agent wasn't started yet (vm still booting)
                    sleep(1)
                else:
                    # this means there's another error with agent, e.g. it is not configured
                    break
            else:
                ifaces = json.loads(qemu_ga_check.stdout[0])
                mgmt_if = next(
                    (
                        i
                        for i in ifaces['return']
                        if i['hardware-address'].lower() == self.mac.lower()
                    ),
                    {},
                )
                try:
                    # get only the ipv4 addresses
                    self.ip_addr = next(
                        i['ip-address']
                        for i in mgmt_if['ip-addresses']
                        if i['ip-address-type'] == 'ipv4'
                    )
                    break
                except (KeyError, StopIteration):
                    sleep(1)
                    continue

        if not self.ip_addr:
            # fallback to avahi in case of any issue with qemu-guest-agent
            logger.warning('Failed to parse the mgmt IPv4 using qemu-guest-agent, trying Avahi')
            result = ssh.command(
                'for i in {{1..60}}; do ping -c1 {0}.local && exit 0; sleep 1;'
                ' done; exit 1'.format(self._target_image),
                ping_from_hostname,
                connection_timeout=30,
            )
            if result.return_code != 0:
                logger.error('Failed to obtain VM IP, reverting changes')
                self.destroy()
                raise VirtualMachineError('Failed to fetch virtual machine IP address information')
            output = ''.join(result.stdout)
            self.ip_addr = output.split('(')[1].split(')')[0]
        ssh_check = ssh.command(
            'for i in {{1..60}}; do nc -vn {0} 22 <<< "" && exit 0; sleep 1;'
            ' done; exit 1'.format(self.ip_addr),
            self.provisioning_server,
            connection_timeout=30,
        )
        if ssh_check.return_code != 0:
            logger.error('Failed to SSH to the VM, reverting changes')
            self.destroy()
            raise VirtualMachineError('Failed to connect to SSH port of the virtual machine')

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        logger.info('Destroying the VM')
        if not self._created:
            return
        if self._subscribed:
            # use try except to unregister the host as in case of host not
            # reachable (or any other failure), the vm is not deleted and this
            # failure will hide any prior failure.
            try:
                self.unregister()
            except Exception as exp:
                logger.error(f'Failed to unregister the host: {self.hostname}\n{exp.message}')

        ssh.command(
            f'virsh destroy {self.target_image}',
            hostname=self.provisioning_server,
            connection_timeout=30,
        )
        ssh.command(
            f'virsh undefine {self.target_image}',
            hostname=self.provisioning_server,
            connection_timeout=30,
        )
        image_name = f'{self.target_image}.img'
        ssh.command(
            'rm {}'.format(os.path.join(self.image_dir, image_name)),
            hostname=self.provisioning_server,
            connection_timeout=30,
        )

    def download_install_rpm(self, repo_url, package_name):
        """Downloads and installs custom rpm on the virtual machine.

        :param repo_url: URL to repository, where package is located.
        :param package_name: Desired package name.
        :return: None.
        :raises robottelo.vm.VirtualMachineError: If package wasn't installed.

        """
        self.run(f'wget -nd -r -l1 --no-parent -A \'{package_name}.rpm\' {repo_url}')
        self.run(f'rpm -i {package_name}.rpm')
        result = self.run(f'rpm -q {package_name}')
        if result.return_code != 0:
            raise VirtualMachineError(f'Failed to install {package_name} rpm.')

    def enable_repo(self, repo, force=False):
        """Enables specified Red Hat repository on the virtual machine. Does
        nothing if capsule or satellite tools repo was passed and downstream
        with custom repo URLs detected (custom repos are enabled by default
        when registering a host).

        :param repo: Red Hat repository name.
        :param force: enforce enabling command, even when custom repos are
            detected for satellite tools or capsule.
        :return: None.

        """
        downstream_repo = None
        if repo == REPOS['rhst6']['id']:
            downstream_repo = settings.sattools_repo['rhel6']
        elif repo == REPOS['rhst7']['id']:
            downstream_repo = settings.sattools_repo['rhel7']
        elif repo in (REPOS['rhsc6']['id'], REPOS['rhsc7']['id']):
            downstream_repo = settings.capsule_repo
        if force or settings.cdn or not downstream_repo:
            self.run(f'subscription-manager repos --enable {repo}')

    def subscription_manager_list_repos(self):
        return self.run("subscription-manager repos --list")

    def subscription_manager_status(self):
        return self.run("subscription-manager status")

    def create_custom_repos(self, **kwargs):
        """Create custom repofiles.
        Each ``kwargs`` item will result in one repository file created. Where
        the key is the repository filename and repository name, and the value
        is the repository URL.

        For example::

            create_custom_repo(custom_repo='http://repourl.domain.com/path')

        Will create a repository file named ``custom_repo.repo`` with
        the following contents::

            [custom_repo]
            name=custom_repo
            baseurl=http://repourl.domain.com/path
            enabled=1
            gpgcheck=0

        """
        for name, url in kwargs.items():
            content = '''[{0}]
name={0}
baseurl={1}
enabled=1
gpgcheck=0'''.format(
                name, url
            )
            self.run(f'echo "{content}" > /etc/yum.repos.d/{name}.repo')

    def install_katello_agent(self):
        """Installs katello agent on the virtual machine.

        :return: None.
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't
            installed.

        """
        wait_for(
            lambda: self.run('yum install -y katello-agent').return_code == 0, timeout=100, delay=2
        )
        result = self.run('rpm -q katello-agent')
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install katello-agent')
        gofer_check = self.run(
            'for i in {1..5}; do service goferd status && exit 0; sleep 1; done; exit 1'
        )
        if gofer_check.return_code != 0:
            raise VirtualMachineError('katello-agent is not running')

    def install_katello_host_tools(self):
        """Installs Katello host tools on the virtual machine

        :raises robottelo.vm.VirtualMachineError: If katello-host-tools wasn't
            installed.
        """
        self.run('yum install -y katello-host-tools')
        result = self.run('rpm -q katello-host-tools')
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install katello-host-tools')

    def install_katello_ca(self):
        """Downloads and installs katello-ca rpm on the virtual machine.

        Uses common helper `install_katello_ca(hostname=None)`, but passes
        `self.ip_addr` instead of the hostname as we are using fake hostnames
        for virtual machines.

        :return: None.
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't
            installed.
        """
        try:
            install_katello_ca(hostname=self.ip_addr)
        except AssertionError:
            raise VirtualMachineError('Failed to download and install the katello-ca rpm')

    def install_capsule_katello_ca(self, capsule=None):
        """Downloads and installs katello-ca rpm on the virtual machine.

        :param: str capsule: Capsule hostname
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't
            installed.
        """
        url = urlunsplit(('http', capsule, 'pub/', '', ''))
        ca_url = urljoin(url, 'katello-ca-consumer-latest.noarch.rpm')
        ssh.command(f'rpm -Uvh {ca_url}', self.ip_addr)
        result = ssh.command(f'rpm -q katello-ca-consumer-{capsule}', self.ip_addr)
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install the katello-ca rpm')

    def register_contenthost(
        self,
        org,
        activation_key=None,
        lce=None,
        consumerid=None,
        force=True,
        releasever=None,
        username=None,
        password=None,
        auto_attach=False,
    ):
        """Registers content host on foreman server using activation-key. This
        can be done in two ways: either by specifying organization name and
        activation key name or by specifying organization name and lifecycle
        environment name (administrator credentials for authentication will be
        passed automatically)

        :param activation_key: Activation key name to register content host
            with.
        :param lce: lifecycle environment name to which register the content
            host.
        :param consumerid: uuid of content host, register to this content host,
            content host has to be created before
        :param org: Organization name to register content host for.
        :param force: Register the content host even if it's already registered
        :param releasever: Set a release version
        :param username: a user name to register the content host with
        :param password: the user password
        :param auto_attach: automatically attach compatible subscriptions to
            this system.
        :return: SSHCommandResult instance filled with the result of the
            registration.
        """
        cmd = f'subscription-manager register --org {org}'
        if activation_key is not None:
            cmd += f' --activationkey {activation_key}'
        elif lce:
            if username is None and password is None:
                username = settings.server.admin_username
                password = settings.server.admin_password

            cmd += f' --environment {lce} --username {username} --password {password}'
            if auto_attach:
                cmd += ' --auto-attach'
        elif consumerid:
            if username is None and password is None:
                username = settings.server.admin_username
                password = settings.server.admin_password

            cmd += ' --consumerid {} --username {} --password {}'.format(
                consumerid, username, password
            )
            if auto_attach:
                cmd += ' --auto-attach'
        else:
            raise VirtualMachineError(
                'Please provide either activation key or lifecycle '
                'environment name to successfully register a host'
            )
        if releasever is not None:
            cmd += f' --release {releasever}'
        if force:
            cmd += ' --force'
        result = self.run(cmd)
        if 'The system has been registered with ID' in ''.join(result.stdout):
            self._subscribed = True
        return result

    def remove_katello_ca(self):
        """Removes katello-ca rpm from the virtual machine.

        Uses common helper `remove_katello_ca(hostname=None)`, but passes
        `self.ip_addr` instead of the hostname as we are using fake hostnames
        for virtual machines.

        :return: None.
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't removed.
        """
        try:
            remove_katello_ca(hostname=self.ip_addr)
        except AssertionError:
            raise VirtualMachineError('Failed to remove the katello-ca rpm')

    def remove_capsule_katello_ca(self, capsule=None):
        """Removes katello-ca rpm and reset rhsm.conf from the virtual machine.

        :param: str capsule: Capsule hostname
        :raises robottelo.vm.VirtualMachineError: If katello-ca wasn't removed.
        """
        ssh.command('yum erase -y $(rpm -qa |grep katello-ca-consumer)', self.ip_addr)
        result = ssh.command(f'rpm -q katello-ca-consumer-{capsule}', self.ip_addr)
        if result.return_code == 0:
            raise VirtualMachineError('Failed to remove the katello-ca rpm')
        rhsm_updates = [
            's/^hostname.*/hostname=subscription.rhn.redhat.com/',
            's|^prefix.*|prefix=/subscription|',
            's|^baseurl.*|baseurl=https://cdn.redhat.com|',
            's/^repo_ca_cert.*/repo_ca_cert=%(ca_cert_dir)sredhat-uep.pem/',
        ]
        for command in rhsm_updates:
            result = ssh.command(f'sed -i -e "{command}" /etc/rhsm/rhsm.conf', self.ip_addr)
            if result.return_code != 0:
                raise VirtualMachineError('Failed to reset the rhsm.conf')

    def unregister(self):
        """Run subscription-manager unregister.

        :return: SSHCommandResult instance filled with the result of the
            unregistration.

        """
        return self.run('subscription-manager unregister')

    def run(self, cmd, timeout=None):
        """Runs a ssh command on the virtual machine

        :param str cmd: Command to run on the virtual machine
        :param int timeout: Time to wait for the ssh command to finish
        :return: A :class:`robottelo.ssh.SSHCommandResult` instance with
            the commands results
        :rtype: robottelo.ssh.SSHCommandResult
        :raises robottelo.vm.VirtualMachineError: If the virtual machine is not
            created.

        """
        if not self._created:
            raise VirtualMachineError(
                'The virtual machine should be created before running any ssh command'
            )

        return ssh.command(cmd, hostname=self.ip_addr, timeout=timeout)

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
        self.run(f'curl -o /etc/yum.repos.d/rhel.repo {rhel_repo}')

    def configure_puppet(self, rhel_repo=None, proxy_hostname=None):
        """Configures puppet on the virtual machine/Host.
        :param proxy_hostname: external capsule hostname
        :param rhel_repo: Red Hat repository link from properties file.
        :return: None.
        """
        if proxy_hostname is None:
            proxy_hostname = settings.server.hostname

        self.configure_rhel_repo(rhel_repo)
        puppet_conf = (
            '[main]\n'
            'vardir = /opt/puppetlabs/puppet/cache\n'
            'logdir = /var/log/puppetlabs/puppet\n'
            'rundir = /var/run/puppetlabs\n'
            'ssldir = /etc/puppetlabs/puppet/ssl\n'
            '[agent]\n'
            'pluginsync      = true\n'
            'report          = true\n'
            'ignoreschedules = true\n'
            f'ca_server       = {proxy_hostname}\n'
            f'certname        = {self.hostname}\n'
            'environment     = production\n'
            f'server          = {proxy_hostname}\n'
        )
        result = self.run('yum install puppet -y')
        if result.return_code != 0:
            raise VirtualMachineError('Failed to install the puppet rpm')
        self.run(f'echo "{puppet_conf}" >> /etc/puppetlabs/puppet/puppet.conf')
        # This particular puppet run on client would populate a cert on
        # sat6 under the capsule --> certifcates or on capsule via cli "puppetserver
        # ca list", so that we sign it.
        self.run('puppet agent -t')
        ssh.command(cmd='puppetserver ca sign --all', hostname=proxy_hostname)
        # This particular puppet run would create the host entity under
        # 'All Hosts' and let's redirect stderr to /dev/null as errors at
        #  this stage can be ignored.
        self.run('puppet agent -t 2> /dev/null')

    def execute_foreman_scap_client(self, policy_id=None):
        """Executes foreman_scap_client on the vm/clients to create security
        audit report.

        :param policy_id: The Id of the OSCAP policy.
        :return: None.

        """
        if policy_id is None:
            result = self.run(
                'awk -F "/" \'/download_path/ {print $4}\' /etc/foreman_scap_client/config.yaml'
            )
            policy_id = result.stdout[0]
        self.run(f'foreman_scap_client {policy_id}', timeout=600)
        if result.return_code != 0:
            raise VirtualMachineError('Failed to execute foreman_scap_client run.')

    def configure_rhai_client(self, activation_key, org, rhel_distro, register=True):
        """Configures a Red Hat Access Insights service on the system by
        installing the redhat-access-insights package and registering to the
        service.

        :param activation_key: Activation key to be used to register the
            system to satellite
        :param org: The org to which the system is required to be registered
        :param rhel_distro: rhel distribution for
        :param register: Whether to register client to insights
        :return: None
        """
        # Download and Install ketello-ca rpm
        self.install_katello_ca()
        self.register_contenthost(org, activation_key)

        # Red Hat Access Insights requires RHEL 6/7/8 repo and it is not
        # possible to sync the repo during the tests, Adding repo file.
        distro_repo_map = {
            DISTRO_RHEL6: settings.rhel6_repo,
            DISTRO_RHEL7: settings.rhel7_repo,
            DISTRO_RHEL8: settings.rhel8_repo,
        }
        rhel_repo = distro_repo_map.get(rhel_distro)

        if rhel_repo is None:
            raise VirtualMachineError(f'Missing RHEL repository configuration for {rhel_distro}.')

        self.configure_rhel_repo(rhel_repo)

        # Install redhat-access-insights package
        package_name = 'insights-client'
        result = self.run(f'yum install -y {package_name}')
        if result.return_code != 0:
            raise VirtualMachineError('Unable to install redhat-access-insights package')

        # Verify if package is installed by query it
        result = self.run(f'rpm -qi {package_name}')
        logger.info(f'Insights client rpm version: {result.stdout}')
        if result.return_code != 0:
            raise VirtualMachineError('Unable to install redhat-access-insights package')

        if not register:
            return

        # Register client with Red Hat Access Insights
        result = self.run('insights-client --register')
        if result.return_code != 0:
            raise VirtualMachineError(
                'Unable to register client to Access Insights through Satellite'
            )

    def set_infrastructure_type(self, infrastructure_type="physical"):
        """Force host to appear as bare-metal or virtual machine in
        subscription-manager fact.

        :param str infrastructure_type: One of "physical", "virtual"
        """
        script_path = "/usr/sbin/virt-what"
        self.run(f"cp -n {script_path} {script_path}.old")

        script_content = ["#!/bin/sh -"]
        if infrastructure_type == "virtual":
            script_content.append("echo kvm")
        script_content = "\n".join(script_content)
        self.run(f"echo -e '{script_content}' > {script_path}")

    def patch_os_release_version(self, distro=DISTRO_RHEL7):
        """Patch VM OS release version.

        This is needed by yum package manager to generate the right RH
        repositories urls.
        """
        if distro == DISTRO_RHEL7:
            rh_product_os_releasever = REPOS['rhel7']['releasever']
        else:
            raise VirtualMachineError('No distro package available to retrieve release version')
        return self.run(
            "touch /etc/yum/vars/releasever "
            "&& echo '{}' > /etc/yum/vars/releasever".format(rh_product_os_releasever)
        )

    def __enter__(self):
        try:
            self.create()
        except Exception as exp:
            # in any case log the exception
            logger.exception(exp)
            self.destroy()
            raise

        return self

    def __exit__(self, *exc):
        self.destroy()
