import importlib
import json
import random
import re
import time
from contextlib import contextmanager
from functools import cached_property
from functools import lru_cache
from pathlib import Path
from pathlib import PurePath
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin
from urllib.parse import urlunsplit

import requests
from box import Box
from broker import Broker
from broker.hosts import Host
from dynaconf.vendor.box.exceptions import BoxKeyError
from fauxfactory import gen_alpha
from fauxfactory import gen_string
from nailgun import entities
from packaging.version import Version
from ssh2.exceptions import AuthenticationError
from wait_for import TimedOutError
from wait_for import wait_for
from wrapanapi.entities.vm import VmState

from robottelo import constants
from robottelo.api.utils import update_provisioning_template
from robottelo.cli.base import Base
from robottelo.cli.factory import CLIFactoryError
from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import robottelo_tmp_dir
from robottelo.config import settings
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS_PATH
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS_VERSION
from robottelo.constants import HAMMER_CONFIG
from robottelo.constants import KEY_CLOAK_CLI
from robottelo.constants import RHSSO_NEW_GROUP
from robottelo.constants import RHSSO_NEW_USER
from robottelo.constants import RHSSO_RESET_PASSWORD
from robottelo.constants import RHSSO_USER_UPDATE
from robottelo.constants import SATELLITE_VERSION
from robottelo.exceptions import DownloadFileError
from robottelo.exceptions import HostPingFailed
from robottelo.host_helpers import CapsuleMixins
from robottelo.host_helpers import ContentHostMixins
from robottelo.host_helpers import SatelliteMixins
from robottelo.logging import logger
from robottelo.utils import validate_ssh_pub_key
from robottelo.utils.datafactory import valid_emails_list
from robottelo.utils.installer import InstallerCommand


POWER_OPERATIONS = {
    VmState.RUNNING: 'running',
    VmState.STOPPED: 'stopped',
    'reboot': 'reboot'
    # TODO paused, suspended, shelved?
}


def get_sat_version():
    """Try to read sat_version from envvar SATELLITE_VERSION
    if not available fallback to ssh connection to get it."""

    try:
        sat_version = Satellite().version
    except (AuthenticationError, ContentHostError, BoxKeyError):
        if hasattr(settings.server.version, 'release'):
            sat_version = str(settings.server.version.release)
        elif hasattr(settings.robottelo, 'satellite_version'):
            sat_version = settings.robottelo.satellite_version
        else:
            sat_version = SATELLITE_VERSION
    return Version('9999' if 'nightly' in sat_version else sat_version)


def get_sat_rhel_version():
    """Try to read rhel_version from Satellite host
    if not available fallback to robottelo configuration."""

    try:
        rhel_version = Satellite().os_version
    except (AuthenticationError, ContentHostError, BoxKeyError):
        if hasattr(settings.server.version, 'rhel_version'):
            rhel_version = str(settings.server.version.rhel_version)
        elif hasattr(settings.robottelo, 'rhel_version'):
            rhel_version = settings.robottelo.rhel_version
    return Version(rhel_version)


def setup_capsule(satellite, capsule, registration_args=None, installation_args=None):
    """Given satellite and capsule instances, run the commands needed to set up the capsule

    Note: This does not perform content setup actions on the Satellite

    :param satellite: An instance of this module's Satellite class
    :param capsule: An instance of this module's Capsule class
    :param registration_args: A dictionary mapping argument: value pairs for registration
    :param installation_args: A dictionary mapping argument: value pairs for installation
    :return: An ssh2-python result object for the installation command.

    """
    if not registration_args:
        registration_args = {}
    file, cmd_args = satellite.capsule_certs_generate(capsule)
    if installation_args:
        cmd_args.update(installation_args)
    satellite.execute(
        f'sshpass -p "{capsule.password}" scp -o "StrictHostKeyChecking no" '
        f'{file} root@{capsule.hostname}:{file}'
    )
    capsule.install_katello_ca(sat_hostname=satellite.hostname)
    capsule.register_contenthost(**registration_args)
    return capsule.install(**cmd_args)


class ContentHostError(Exception):
    pass


class CapsuleHostError(Exception):
    pass


class SatelliteHostError(Exception):
    pass


class ContentHost(Host, ContentHostMixins):
    run = Host.execute
    default_timeout = settings.server.ssh_client.command_timeout

    def __init__(self, hostname, auth=None, **kwargs):
        """ContentHost object with optional ssh connection

        :param hostname: The fqdn of a ContentHost target
        :param auth: ('root', 'rootpass') or '/path/to/keyfile.rsa'
        :param satellite: optional parameter satellite object.
        """
        if not hostname:
            raise ContentHostError('A valid hostname must be provided')
        if isinstance(auth, tuple):
            # username/password-based auth
            kwargs.update({'username': auth[0], 'password': auth[1]})
        elif isinstance(auth, str):
            # key file based authentication
            kwargs.update({'key_filename': auth})
        self._satellite = kwargs.get('satellite')
        self.blank = kwargs.get('blank', False)
        super().__init__(hostname=hostname, **kwargs)

    @property
    def satellite(self):
        if not self._satellite:
            self._satellite = Satellite()
        return self._satellite

    @property
    def nailgun_host(self):
        """If this host is subscribed, provide access to its nailgun object"""
        if self.subscribed:
            try:
                host_list = self.satellite.api.Host().search(query={'search': self.hostname})[0]
            except Exception as err:
                logger.error(f'Failed to get nailgun host for {self.hostname}: {err}')
                host_list = None
            return host_list

    @property
    def subscribed(self):
        """Boolean representation of a content host's subscription status"""
        return 'Status: Unknown' not in self.execute('subscription-manager status').stdout

    @property
    def ip_addr(self):
        ipv4, *ipv6 = self.execute('hostname -I').stdout.split()
        return ipv4

    @cached_property
    def _redhat_release(self):
        """Process redhat-release file for distro and version information"""
        result = self.execute('cat /etc/redhat-release')
        if result.status != 0:
            raise ContentHostError(f'Not able to cat /etc/redhat-release "{result.stderr}"')
        match = re.match(r'(?P<distro>.+) release (?P<major>\d+)(.(?P<minor>\d+))?', result.stdout)
        if match is None:
            raise ContentHostError(f'Not able to parse release string "{result.stdout}"')
        return match.groupdict()

    @cached_property
    def os_distro(self):
        """Get host's distro information"""
        groups = self._redhat_release
        return groups['distro']

    @cached_property
    def os_version(self):
        """Get host's OS version information

        :returns: A ``packaging.version.Version`` instance
        """
        groups = self._redhat_release
        minor_version = '' if groups['minor'] is None else f'.{groups["minor"]}'
        version_string = f'{groups["major"]}{minor_version}'
        return Version(version=version_string)

    def setup(self):
        if not self.blank:
            self.remove_katello_ca()

    def teardown(self):
        if not self.blank:
            if self.nailgun_host:
                self.nailgun_host.delete()
            self.unregister()
        # Strip most unnecessary attributes from our instance for checkin
        keep_keys = set(self.to_dict()) | {'release', '_prov_inst', '_cont_inst'}
        self.__dict__ = {k: v for k, v in self.__dict__.items() if k in keep_keys}
        self.__class__ = Host

    def power_control(self, state=VmState.RUNNING, ensure=True):
        """Lookup the host workflow for power on and execute

        Args:
            state: A VmState from wrapanapi.entities.vm or 'reboot'
            ensure: boolean indicating whether to try and connect to ensure power state

        Raises:
            NotImplementedError: if the workflow name isn't found in settings
            BrokerError: various error types to do with broker execution
            ContentHostError: if the workflow status isn't successful and broker didn't raise
        """
        try:
            vm_operation = POWER_OPERATIONS.get(state)
            workflow_name = settings.broker.host_workflows.power_control
        except (AttributeError, KeyError):
            raise NotImplementedError(
                'No workflow in broker.host_workflows for power control, '
                'or VM operation not supported'
            )
        assert (
            # TODO read the kwarg name from settings too?
            Broker()
            .execute(
                workflow=workflow_name,
                vm_operation=vm_operation,
                source_vm=self.name,
            )['status']
            .lower()
            == 'successful'
        )

        if ensure and state in [VmState.RUNNING, 'reboot']:
            try:
                wait_for(
                    self.connect, fail_condition=lambda res: res is not None, handle_exception=True
                )
            # really broad diaper here, but connection exceptions could be a ton of types
            except TimedOutError:
                raise ContentHostError('Unable to connect to host that should be running')

    def download_file(self, file_url, local_path=None, file_name=None):
        """Downloads file from given fileurl to directory specified by local_path by given filename
        on satellite.

        If remote directory is not specified it downloads file to /tmp/.

        :param str file_url: The complete server file path from where the
            file will be downloaded.
        :param str local_path: Name of directory where file will be saved. If not
            provided file will be saved in /tmp/ directory.
        :param str file_name: New name of the Downloaded file else its given from file_url

        :returns: Returns list containing complete file path and name of downloaded file.
        """
        file_name = PurePath(file_name or file_url).name
        local_path = PurePath(local_path or '/tmp') / file_name

        # download on server
        result = self.execute(f'wget -O {local_path} {file_url}')
        if result.status != 0:
            raise DownloadFileError(f'Unable to download {file_name}: {result.stderr}')
        return local_path, file_name

    def download_install_rpm(self, repo_url, package_name):
        """Downloads and installs custom rpm on the broker virtual machine.

        :param repo_url: URL to repository, where package is located.
        :param package_name: Desired package name.
        :return: None.
        :raises robottelo.hosts.ContentHostError: If package wasn't installed.

        """
        self.execute(f'curl -O {repo_url}/{package_name}.rpm')
        result = self.execute(f'rpm -i {package_name}.rpm')
        if result.status != 0:
            raise ContentHostError(f'Failed to install {package_name} rpm.')

    def download_repos(self, repo_name, version):
        """Downloads the satellite or capsule repos on the machine
        :param repo_name: satellite or capsule repo_name
        :param vesion: rhel version
        """
        repo_location = (
            f'{settings.repos.ohsnap_repo_host}/api/releases/'
            f'{self.satellite.version}/el{version}/{repo_name}/repo_file'
        )
        if repo_name in ('satellite', 'capsule'):
            self.execute(f'curl -o /etc/yum.repos.d/{repo_name}.repo {repo_location}')
        else:
            raise ValueError("Invalid repo_name, must be of value satellite or capsule")

    def enable_repo(self, repo, force=False):
        """Enables specified Red Hat repository on the broker virtual machine.
        Does nothing if downstream capsule or satellite tools repo was passed.
        Custom repos are enabled by default when registering a host.

        :param repo: Red Hat repository name.
        :param force: enforce enabling command, even when custom repos are
            detected for satellite tools or capsule.
        :return: None.

        """
        downstream_repo = None
        if repo == constants.REPOS['rhst6']['id']:
            downstream_repo = settings.repos.sattools_repo['rhel6']
        elif repo == constants.REPOS['rhst7']['id']:
            downstream_repo = settings.repos.sattools_repo['rhel7']
        elif repo == constants.REPOS['rhst8']['id']:
            downstream_repo = settings.repos.sattools_repo['rhel8']
        elif repo in (constants.REPOS['rhsc6']['id'], constants.REPOS['rhsc7']['id']):
            downstream_repo = settings.repos.capsule_repo
        if force or settings.robottelo.cdn or not downstream_repo:
            return self.execute(f'subscription-manager repos --enable {repo}')

    def subscription_manager_list_repos(self):
        return self.execute('subscription-manager repos --list')

    def subscription_manager_status(self):
        return self.execute('subscription-manager status')

    def subscription_manager_list(self):
        return self.execute('subscription-manager list')

    def subscription_manager_get_pool(self, sub_list=[]):
        """
        Return pool ids for the corresponding subscriptions in the list
        """
        pool_ids = []
        for sub in sub_list:
            result = self.execute(
                f'subscription-manager list --available --pool-only --matches="{sub}"'
            )
            result = result.stdout
            result = result.split('\n')
            result = ' '.join(result).split()
            pool_ids.append(result)
        return pool_ids

    def subscription_manager_attach_pool(self, pool_list=[]):
        """
        Attach pool ids to the host and return the result
        """
        result = []
        for pool in pool_list:
            result.append(self.execute(f'subscription-manager attach --pool={pool}'))
        return result

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
            content = f'[{name}]\n' f'name={name}\n' f'baseurl={url}\n' 'enabled=1\n' 'gpgcheck=0'
            self.execute(f'echo "{content}" > /etc/yum.repos.d/{name}.repo')

    def get_base_url_for_older_rhel_minor(self):
        domain = settings.repos.rhel_os_repo_host
        major = self.os_version.major
        minor = self.os_version.minor - 1
        if major == 8:
            baseurl = (
                f'{domain}/rhel-{major}/rel-eng/RHEL-{major}/'
                f'latest-RHEL-{major}.{minor}.0/compose/AppStream/x86_64/os/'
            )
        elif major == 7:
            baseurl = (
                f'{domain}/rhel-{major}/rel-eng/RHEL-{major}/'
                f'latest-RHEL-{major}.{minor}/compose/Server/x86_64/os/'
            )
        else:
            raise ValueError('not supported major version')
        return baseurl

    def install_katello_agent(self):
        """Install katello-agent on the virtual machine.

        :return: None.
        :raises ContentHostError: if katello-agent is not installed.
        """
        result = self.execute('yum install -y katello-agent')
        if result.status != 0:
            raise ContentHostError(f'Failed to install katello-agent: {result.stdout}')
        if getattr(self, '_cont_inst', None):
            # We're running in a container, goferd won't be running as a service
            # so let's run it in the foreground, then detach from the exec
            self._cont_inst.exec_run('goferd -f', detach=True)
        else:
            # We're in a traditional VM, so goferd should be running after katello-agent install
            try:
                wait_for(lambda: self.execute('service goferd status').status == 0)
            except TimedOutError:
                raise ContentHostError('katello-agent is not running')

    def install_katello_host_tools(self):
        """Installs Katello host tools on the broker virtual machine

        :raises robottelo.hosts.ContentHostError: If katello-host-tools wasn't
            installed.
        """
        result = self.execute('yum install -y katello-host-tools')
        if result.status != 0:
            raise ContentHostError('Failed to install katello-host-tools')

    def install_katello_ca(self, satellite):
        """Downloads and installs katello-ca rpm on the content host.

        :param str satellite: robottelo.hosts.Satellite instance

        :return: None.
        :raises robottelo.hosts.ContentHostError: If katello-ca wasn't
            installed.
        """
        self._satellite = satellite
        self.execute(
            f'curl --insecure --output katello-ca-consumer-latest.noarch.rpm \
                    {satellite.url_katello_ca_rpm}'
        )
        # check if the host is fips-enabled
        result = self.execute('sysctl crypto.fips_enabled')
        if 'crypto.fips_enabled = 1' in result.stdout:
            self.execute('rpm -Uvh --nodigest --nofiledigest katello-ca-consumer-latest.noarch.rpm')
        else:
            self.execute('rpm -Uvh katello-ca-consumer-latest.noarch.rpm')
        # Not checking the status here, as rpm could be installed before
        # and installation may fail
        result = self.execute(f'rpm -q katello-ca-consumer-{satellite.hostname}')
        # Checking the status here to verify katello-ca rpm is actually
        # present in the system
        if satellite.hostname not in result.stdout:
            raise ContentHostError('Failed to download and install the katello-ca rpm')

    def remove_katello_ca(self):
        """Removes katello-ca rpm from the broker virtual machine.

        :return: None.
        :raises robottelo.hosts.ContentHostError: If katello-ca wasn't removed.
        """
        # Not checking the status here, as rpm can be not even installed
        # and deleting may fail
        self.execute('yum erase -y $(rpm -qa |grep katello-ca-consumer)')
        # Checking the status here to verify katello-ca rpm is actually
        # not present in the system
        result = self.execute('rpm -qa |grep katello-ca-consumer')
        if result.status == 0:
            raise ContentHostError(f'katello-ca rpm(s) are still installed: {result.stdout}')
        self.execute('subscription-manager clean')
        self._satellite = None

    def install_capsule_katello_ca(self, capsule=None):
        """Downloads and installs katello-ca rpm on the broker virtual machine.

        :param: str capsule: Capsule hostname
        :raises robottelo.hosts.ContentHostError: If katello-ca wasn't
            installed.
        """
        url = urlunsplit(('http', capsule, 'pub/', '', ''))
        ca_url = urljoin(url, 'katello-ca-consumer-latest.noarch.rpm')
        result = self.execute(f'rpm -Uvh {ca_url}')
        if result.status != 0:
            raise ContentHostError('Failed to install the katello-ca rpm')

    def install_cockpit(self):
        """Installs cockpit on the broker virtual machine.

        :raises robottelo.hosts.ContentHostError: If cockpit wasn't
            installed.
        """
        result = self.execute('yum install cockpit -y')
        if result.status != 0:
            raise ContentHostError('Failed to install the cockpit')

    def register_contenthost(
        self,
        org='Default_Organization',
        activation_key=None,
        lce='Library',
        consumerid=None,
        force=True,
        releasever=None,
        name=None,
        username=settings.server.admin_username,
        password=settings.server.admin_password,
        auto_attach=False,
    ):
        """Registers content host on foreman server either by specifying
        organization name and activation key name or by specifying organization
        name and lifecycle environment name (administrator credentials for
        authentication will be passed automatically).

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
        :param name: name of the system to register, defaults to the hostname
        :return: SSHCommandResult instance filled with the result of the
            registration.
        """

        if username and password:
            userpass = f' --username {username} --password {password}'
        else:
            userpass = ''
        # Setup the base command
        cmd = 'subscription-manager register'
        if org:
            cmd += f' --org {org}'
        # Determine our registration path
        if activation_key:
            cmd += f' --activationkey {activation_key}'
        elif lce:
            cmd += f' --environment {lce}{userpass}'
        elif consumerid:
            cmd += f' --consumerid {consumerid}{userpass}'
        else:
            # if no other methods are provided, we can still try user/pass
            cmd += userpass
        # Additional registration modifiers
        if auto_attach:
            cmd += ' --auto-attach'
        if releasever:
            cmd += f' --release {releasever}'
        if force:
            cmd += ' --force'
        if name:
            cmd += f' --name {name}'
        return self.execute(cmd)

    def unregister(self):
        """Run subscription-manager unregister.

        :return: SSHCommandResult instance filled with the result of the
            unregistration.

        """
        return self.execute('subscription-manager unregister')

    def get(self, remote_path, local_path=None):
        """Get a remote file from the broker virtual machine."""
        self.session.sftp_read(source=remote_path, destination=local_path)

    def put(self, local_path, remote_path=None):
        """Put a local file to the broker virtual machine.
        If local_path is a manifest object, write its contents to a temporary file
        then continue with the upload.
        """
        if 'manifests.Manifest' in str(local_path):
            with NamedTemporaryFile(dir=robottelo_tmp_dir) as content_file:
                content_file.write(local_path.content.read())
                content_file.flush()
                self.session.sftp_write(source=content_file.name, destination=remote_path)
        else:
            self.session.sftp_write(source=local_path, destination=remote_path)

    def put_ssh_key(self, source_key_path, destination_key_name):
        """Copy ssh key to virtual machine ssh path and ensure proper permission is set

        Args:
            source_key_path: The ssh key file path to copy to vm
            destination_key_name: The ssh key file name when copied to vm
        """
        destination_key_path = f'/root/.ssh/{destination_key_name}'
        self.put(local_path=source_key_path, remote_path=destination_key_path)
        result = self.execute(f'chmod 600 {destination_key_path}')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to chmod ssh key file:\n{result.stderr}')

    def add_authorized_key(self, pub_key):
        """Inject a public key into the authorized keys file

        Args:
            pub_key: public key string, file-like object, or path string
        Raises:
            ValueError: if the pub_key isn't valid or found
        """
        if getattr(pub_key, 'read', False):  # key is a file-like object
            key_content = pub_key.read()
        elif validate_ssh_pub_key(pub_key):  # key is a valid key-string
            key_content = pub_key
        # use expanduser here to handle relative paths with ~ resolving locally
        elif Path(pub_key).expanduser().exists():  # key is a path to a pub key-file
            key_content = Path(pub_key).expanduser().read_text()
        else:
            raise ValueError('Invalid key')
        key_content = key_content.strip()
        ssh_path = PurePath('~/.ssh')
        auth_file = ssh_path.joinpath('authorized_keys')
        # ensure ssh directory exists
        self.execute(f'mkdir -p {ssh_path}')
        # append the key if doesn't exists
        self.execute(
            "grep -q '{key}' {dest} || echo '{key}' >> {dest}".format(
                key=key_content, dest=auth_file
            )
        )
        # set proper permissions
        self.execute(f'chmod 700 {ssh_path}')
        self.execute(f'chmod 600 {auth_file}')
        self.execute(f'chown -R {self.username} {ssh_path}')
        # Restore SELinux context with restorecon, if it's available:
        self.execute(f'command -v restorecon && restorecon -RvF {ssh_path} || true')

    def add_rex_key(self, satellite, key_path=None):
        """Read a public key from the passed Satellite, and add it to authorized_keys

        Args:
            satellite: ``Capsule`` or ``Satellite`` instance
            key_path: optional path to the key on the satellite
        """
        if key_path is not None:
            sat_key = satellite.execute(f'cat {key_path}').stdout.strip()
        else:
            sat_key = satellite.rex_pub_key
        self.add_authorized_key(pub_key=sat_key)

    def update_known_hosts(self, ssh_key_name, host, user=None):
        """Create host entry in vm ssh config and known_hosts files to allow vm
        to access host via ssh without password prompt

        :param robottelo.hosts.ContentHost vm: Virtual machine instance
        :param str ssh_key_name: The ssh key file name to use to access host,
            the file must already exist in /root/.ssh directory
        :param str host: the hostname to setup that will be accessed from vm
        :param str user: the user that will access the host
        """
        user = user or 'root'
        ssh_path = '/root/.ssh'
        ssh_key_file_path = f'{ssh_path}/{ssh_key_name}'
        # setup the config file
        ssh_config_file_path = f'{ssh_path}/config'
        result = self.execute(f'touch {ssh_config_file_path}')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to create ssh config file:\n{result.stderr}')
        result = self.execute(
            f'echo "\nHost {host}\n\tHostname {host}\n\tUser {user}\n'
            f'\tIdentityFile {ssh_key_file_path}\n" >> {ssh_config_file_path}'
        )
        if result.status != 0:
            raise CLIFactoryError(f'Failed to write to ssh config file:\n{result.stderr}')
        # add host entry to ssh known_hosts
        result = self.execute(f'ssh-keyscan {host} >> {ssh_path}/known_hosts')
        if result.status != 0:
            raise CLIFactoryError(
                f'Failed to put hostname in ssh known_hosts files:\n{result.stderr}'
            )

    def configure_puppet(self, proxy_hostname=None):
        """Configures puppet on the virtual machine/Host.
        :param proxy_hostname: external capsule hostname
        :return: None.
        :raises robottelo.hosts.ContentHostError: If installation or configuration fails.
        """
        if proxy_hostname is None:
            proxy_hostname = settings.server.hostname

        self.create_custom_repos(
            sat_client=settings.repos['SATCLIENT_REPO'][f'RHEL{self.os_version.major}']
        )
        result = self.execute('yum install puppet-agent -y')
        if result.status != 0:
            raise ContentHostError('Failed to install the puppet-agent rpm')

        cert_name = self.hostname
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
            f'certname        = {cert_name}\n'
            'environment     = production\n'
            f'server          = {proxy_hostname}\n'
        )
        self.execute(f'echo "{puppet_conf}" >> /etc/puppetlabs/puppet/puppet.conf')

        # This particular puppet run on client would populate a cert on
        # sat6 under the capsule --> certifcates or on capsule via cli "puppetserver
        # ca list", so that we sign it.
        self.execute('/opt/puppetlabs/bin/puppet agent -t')
        proxy_host = Host(proxy_hostname)
        proxy_host.execute(f'puppetserver ca sign --certname {cert_name}')
        # This particular puppet run would create the host entity under
        # 'All Hosts' and let's redirect stderr to /dev/null as errors at
        #  this stage can be ignored.
        result = self.execute('/opt/puppetlabs/bin/puppet agent -t 2> /dev/null')
        if result.status:
            raise ContentHostError('Failed to configure puppet on the content host')

    def execute_foreman_scap_client(self, policy_id=None):
        """Executes foreman_scap_client on the vm to create security audit report.

        :param policy_id: The Id of the OSCAP policy.
        :return: None.

        """
        if policy_id is None:
            result = self.execute(
                'awk -F "/" \'/download_path/ {print $4}\' /etc/foreman_scap_client/config.yaml'
            )
            policy_id = result.stdout.strip()
        result = self.execute(f'foreman_scap_client ds {policy_id}')
        if result.status != 0:
            data = self.execute(
                'rpm -qa |grep scap; yum repolist;cat /etc/foreman_scap_client/config.yaml; '
                'cat /etc/cron.d/foreman_scap_client_cron; tail -n 100 /var/log/messages'
            )
            raise ContentHostError(
                f'Failed to execute foreman_scap_client run. '
                f'Command exited with code: {result.status}, stderr: {result.stderr}, '
                f'stdout: {result.stdout} host_data_stdout: {data.stdout}, '
                f'and host_data_stderr: {data.stderr}'
            )

    def configure_rex(self, satellite, org, subnet_id=None, by_ip=True, register=True):
        """Setup a VM host for remote execution.

        :param Satellite satellite: a hosts.Satellite instance
        :param str org: The organization entity, label attr is used
        :param int subnet: (Optional) Nailgun subnet entity id, to be used by the vm_client host.
        :param bool by_ip: Whether remote execution will use ip or host name to access server.
        :param bool register: Whether to register to the Satellite. Keyexchange done regardless
        """
        if register:
            self.install_katello_ca(satellite)
            self.register_contenthost(org.label, lce='Library')
            assert self.subscribed
        self.add_rex_key(satellite=satellite)
        if register and subnet_id is not None:
            host = self.nailgun_host.read()
            host.name = self.hostname
            host.subnet_id = int(subnet_id)
            host.update(['name', 'subnet_id'])
        if register and by_ip:
            # connect to host by ip
            host = self.nailgun_host.read()
            host_parameters = [
                {
                    'name': 'remote_execution_connect_by_ip',
                    'value': 'True',
                    'parameter-type': 'boolean',
                }
            ]
            host.host_parameters_attributes = host_parameters
            host.update(['host_parameters_attributes'])

    def configure_rhai_client(
        self, satellite, activation_key, org, rhel_distro, register_insights=True, register=True
    ):
        """Configures a Red Hat Access Insights service on the system by
        installing the redhat-access-insights package and registering to the
        service.

        :param activation_key: Activation key to be used to register the
            system to satellite
        :param org: The org to which the system is required to be registered
        :param rhel_distro: rhel distribution used by the vm
        :param register: Whether to register client to insights
        :return: None
        """
        if register:
            # Install Satellite CA rpm
            self.install_katello_ca(satellite)

            self.register_contenthost(org, activation_key)

        # Red Hat Insights requires RHEL 6/7/8 repo and it is not
        # possible to sync the repo during the tests, Adding repo file.
        distro_repo_map = {
            constants.DISTRO_RHEL6: settings.repos.rhel6_os,
            constants.DISTRO_RHEL7: settings.repos.rhel7_os,
            constants.DISTRO_RHEL8: settings.repos.rhel8_os,
            constants.DISTRO_RHEL9: settings.repos.rhel9_os,
        }
        rhel_repo = distro_repo_map.get(rhel_distro)

        if rhel_repo is None:
            raise ContentHostError(f'Missing RHEL repository configuration for {rhel_distro}.')

        if rhel_distro not in (constants.DISTRO_RHEL6, constants.DISTRO_RHEL7):
            self.create_custom_repos(**rhel_repo)
        else:
            self.create_custom_repos(**{rhel_distro: rhel_repo})

        # Install insights-client rpm
        if self.execute('yum install -y insights-client').status != 0:
            raise ContentHostError('Unable to install insights-client rpm')

        if register_insights:
            # Register client
            if self.execute('insights-client --register').status != 0:
                raise ContentHostError('Unable to register client to Insights through Satellite')

    def unregister_insights(self):
        """Unregister insights client.

        :return: None
        """
        result = self.execute('insights-client --unregister')
        if result.status != 0:
            raise ContentHostError('Failed to unregister client from Insights through Satellite')

    def set_infrastructure_type(self, infrastructure_type='physical'):
        """Force host to appear as bare-metal orbroker virtual machine in
        subscription-manager fact.

        :param str infrastructure_type: One of 'physical', 'virtual'
        """
        script_path = '/usr/sbin/virt-what'
        self.execute(f'cp -n {script_path} {script_path}.old')

        script_content = ['#!/bin/sh -']
        if infrastructure_type == 'virtual':
            script_content.append('echo kvm')
        script_content = '\n'.join(script_content)
        self.execute(f"echo -e '{script_content}' > {script_path}")

    def patch_os_release_version(self, distro=constants.DISTRO_RHEL7):
        """Patch VM OS release version.

        This is needed by yum package manager to generate the right RH
        repositories urls.
        """
        if distro == constants.DISTRO_RHEL7:
            rh_product_os_releasever = constants.REPOS['rhel7']['releasever']
        else:
            raise ContentHostError('No distro package available to retrieve release version')
        return self.execute(f"echo '{rh_product_os_releasever}' > /etc/yum/vars/releasever")

    # What the heck to call this function?
    def contenthost_setup(
        self,
        satellite,
        org_label,
        location_title=None,
        rh_repo_ids=None,
        repo_labels=None,
        product_label=None,
        lce=None,
        activation_key=None,
        patch_os_release_distro=None,
        install_katello_agent=True,
    ):
        """
        Setup a Content Host with basic components and tasks.

        :param str org_label: The Organization label.
        :param list rh_repo_ids: a list of RH repositories ids to enable.
        :param list repo_labels: a list of custom repositories labels to enable.
        :param str product_label: product label if repos_label is applicable.
        :param str lce: Lifecycle environment label if applicable.
        :param str activation_key: Activation key name if applicable.
        :param str patch_os_release_distro: distro name, to patch the VM with os version.
        :param bool install_katello_agent: whether to install katello agent.
        """
        rh_repo_ids = rh_repo_ids or []
        repo_labels = repo_labels or []
        if location_title:
            self.set_facts({'locations.facts': {'foreman_location': str(location_title)}})
        self.install_katello_ca(satellite)
        result = self.register_contenthost(org_label, activation_key=activation_key, lce=lce)
        if not self.subscribed:
            logger.info(result.stdout)
            raise CLIFactoryError('Virtual machine failed subscription')
        if patch_os_release_distro:
            self.patch_os_release_version(distro=patch_os_release_distro)
        # Enable RH repositories
        for repo_id in rh_repo_ids:
            self.enable_repo(repo_id, force=True)
        if product_label:
            # Enable custom repositories
            for repo_label in repo_labels:
                result = self.execute(
                    f'yum-config-manager --enable {org_label}_{product_label}_{repo_label}'
                )
                if result.status != 0:
                    raise CLIFactoryError(
                        f'Failed to enable custom repository {repo_label!s}\n{result.stderr}'
                    )
        if install_katello_agent:
            self.install_katello_agent()

    def virt_who_hypervisor_config(
        self,
        satellite,
        config_id,
        org_id=None,
        lce_id=None,
        hypervisor_hostname=None,
        configure_ssh=False,
        hypervisor_user=None,
        subscription_name=None,
        exec_one_shot=False,
        upload_manifest=True,
        extra_repos=None,
    ):
        """
        Configure virtual machine as hypervisor virt-who service

        :param int config_id: virt-who config id
        :param int org_id: the organization id
        :param int lce_id: the lifecycle environment id to use
        :param str hypervisor_hostname: the hypervisor hostname
        :param str hypervisor_user: hypervisor user that connect with the ssh key
        :param bool configure_ssh: configure the ssh key to allow host to connect to hypervisor
        :param str subscription_name: the subscription name to assign to virt-who hypervisor guests
        :param bool exec_one_shot: whether to run the virt-who one-shot command after startup
        :param bool upload_manifest: whether to upload the organization manifest
        :param list extra_repos: (Optional) repositories dict options to setup additionally.
        """
        from robottelo.cli.org import Org
        from robottelo.cli import factory as cli_factory
        from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
        from robottelo.cli.subscription import Subscription
        from robottelo.cli.virt_who_config import VirtWhoConfig

        org = cli_factory.make_org() if org_id is None else Org.info({'id': org_id})

        if lce_id is None:
            lce = cli_factory.make_lifecycle_environment({'organization-id': org['id']})
        else:
            lce = LifecycleEnvironment.info({'id': lce_id, 'organization-id': org['id']})
        extra_repos = extra_repos or []
        repos = [
            # Red Hat Satellite Tools
            {
                'product': constants.PRDS['rhel'],
                'repository-set': constants.REPOSET['rhst7'],
                'repository': constants.REPOS['rhst7']['name'],
                'repository-id': constants.REPOS['rhst7']['id'],
                'url': settings.repos.sattools_repo['rhel7'],
                'cdn': settings.robottelo.cdn or not settings.repos.sattools_repo['rhel7'],
            }
        ]
        repos.extend(extra_repos)
        content_setup_data = cli_factory.setup_cdn_and_custom_repos_content(
            org['id'],
            lce['id'],
            repos,
            upload_manifest=upload_manifest,
            rh_subscriptions=[constants.DEFAULT_SUBSCRIPTION_NAME],
        )
        activation_key = content_setup_data['activation_key']
        content_view = content_setup_data['content_view']
        self.contenthost_setup(
            satellite=satellite,
            org_label=org['label'],
            activation_key=activation_key['name'],
            patch_os_release_distro=constants.DISTRO_RHEL7,
            rh_repo_ids=[repo['repository-id'] for repo in repos if repo['cdn']],
            install_katello_agent=False,
        )
        # configure manually RHEL custom repo url as sync time is very big
        # (more than 2 hours for RHEL 7Server) and not critical in this context.
        rhel_repo_option_name = (
            f'rhel{constants.DISTROS_MAJOR_VERSION[constants.DISTRO_RHEL7]}_repo'
        )
        rhel_repo_url = getattr(settings.repos, rhel_repo_option_name, None)
        if not rhel_repo_url:
            raise ValueError(
                f'Settings option "{rhel_repo_option_name}" is whether not set or does not exist'
            )
        self.create_custom_repos(rhel7=rhel_repo_url)
        if hypervisor_hostname and configure_ssh:
            # configure ssh access of hypervisor from self
            hypervisor_ssh_key_name = f'hypervisor-{gen_alpha().lower()}.key'
            # upload the ssh key
            self.put_ssh_key(settings.server.ssh_key, hypervisor_ssh_key_name)
            # setup the ssh config and known_hosts files
            self.update_known_hosts(
                hypervisor_ssh_key_name, hypervisor_hostname, user=hypervisor_user
            )

        # upload the virt-who config deployment script
        virt_who_deploy_directory = '/root/virt_who_deploy_output'
        virt_who_deploy_filename = f'{gen_alpha(length=5)}-virt-who-deploy-{config_id}'
        virt_who_deploy_file = f'{virt_who_deploy_directory}/{virt_who_deploy_filename}'
        # create the virt-who directory on the broker VM
        self.execute(f'mkdir -p {virt_who_deploy_directory}')
        # create the virt-who directory on satellite
        satellite = Satellite()
        satellite.execute(f'mkdir -p {virt_who_deploy_directory}')
        VirtWhoConfig.fetch({'id': config_id, 'output': virt_who_deploy_file})
        # remote_copy from satellite to self
        satellite.session.remote_copy(virt_who_deploy_file, self)

        # ensure the virt-who config deploy script is executable
        result = self.execute(f'chmod +x {virt_who_deploy_file}')
        if result.status != 0:
            raise CLIFactoryError(
                f'Failed to set deployment script as executable:\n{result.stderr}'
            )
        # execute the deployment script
        result = self.execute(f'{virt_who_deploy_file}')
        if result.status != 0:
            raise CLIFactoryError(f'Deployment script failure:\n{result.stderr}')
        # after this step, we should have virt-who service installed and started
        if exec_one_shot:
            # usually to be sure that the virt-who generated the report we need
            # to force a one shot report, for this we have to stop the virt-who
            # service
            result = self.execute('service virt-who stop')
            if result.status != 0:
                raise CLIFactoryError(f'Failed to stop the virt-who service:\n{result.stderr}')
            result = self.execute('virt-who --one-shot', timeout=900000)
            if result.status != 0:
                raise CLIFactoryError(
                    f'Failed when executing virt-who --one-shot:\n{result.stderr}'
                )
            result = self.execute('service virt-who start')
            if result.status != 0:
                raise CLIFactoryError(f'Failed to start the virt-who service:\n{result.stderr}')
        # after this step the hypervisor as a content host should be created
        # do not confuse virt-who host with hypervisor host as they can be
        # diffrent hosts and as per this setup we have only registered the virt-who
        # host, the hypervisor host should registered after virt-who send the
        # first report when started or with one shot command
        # the virt-who hypervisor will be registered to satellite with host name
        # like "virt-who-{hypervisor_hostname}-{organization_id}"
        virt_who_hypervisor_hostname = f'virt-who-{hypervisor_hostname}-{org["id"]}'
        # find the registered virt-who hypervisor host
        org_hosts = entities.Host().search(
            query={'search': f'organization_id={org["id"]} and name={virt_who_hypervisor_hostname}'}
        )
        # Note: if one shot command was executed the report is immediately
        # generated, and the server must have already registered the virt-who
        # hypervisor host
        if not org_hosts and not exec_one_shot:
            # we have to wait until the first report was sent.
            # the report is generated after the virt-who service startup, but some
            # small delay can occur.
            max_time = time.time() + 60
            while time.time() <= max_time:
                time.sleep(5)
                org_hosts = entities.Host().search(
                    query={
                        'search': f'organization_id={org["id"]}'
                        f' and name={virt_who_hypervisor_hostname}'
                    }
                )
                if org_hosts:
                    break

        if len(org_hosts) == 0:
            raise CLIFactoryError(f'Failed to find hypervisor host:\n{result.stderr}')
        virt_who_hypervisor_host = org_hosts[0]
        subscription_id = None
        if hypervisor_hostname and subscription_name:
            subscriptions = Subscription.list({'organization-id': org_id}, per_page=False)
            for subscription in subscriptions:
                if subscription['name'] == subscription_name:
                    subscription_id = subscription['id']
                    Host.subscription_attach(
                        {'host': virt_who_hypervisor_hostname, 'subscription-id': subscription_id}
                    )
                    break
        return {
            'subscription_id': subscription_id,
            'subscription_name': subscription_name,
            'activation_key_id': activation_key['id'],
            'organization_id': org['id'],
            'content_view_id': content_view['id'],
            'lifecycle_environment_id': lce['id'],
            'virt_who_hypervisor_host': virt_who_hypervisor_host,
        }

    def custom_cert_generate(self, capsule_hostname):
        """copy all configuration files to satellite host for generating custom certs"""
        self.execute(f'mkdir ssl-build/{capsule_hostname}')
        for file in [
            'generate-ca.sh',
            'generate-crt.sh',
            'openssl.cnf',
            'certs.sh',
            'extensions.txt',
        ]:
            self.session.sftp_write(PurePath('tests/foreman/data').joinpath(file), f'/root/{file}')
        self.execute('echo 100001 > serial')
        self.execute('bash generate-ca.sh')
        result = self.execute(f'yes | bash generate-crt.sh {self.hostname}')
        assert result.status == 0
        result = self.execute('bash certs.sh')
        assert result.status == 0

    def custom_certs_cleanup(self):
        """cleanup all cert configuration files"""
        files = [
            'cacert.crt',
            'cacert.crt',
            'certindex*',
            'generate-*.sh',
            'capsule_cert',
            'openssl.cnf',
            'private',
            'serial*',
            'certs/*',
            'extensions.txt',
            'certs',
            'certs.sh',
            self.hostname,
        ]
        self.execute(f'cd /root && rm -rf {" ".join(files)}')

    def install_tracer(self):
        """Install tracer on the host, prerequisites the katello host tools needs to be installed"""
        cmd_result = self.execute('yum install -y katello-host-tools-tracer')
        if cmd_result.status != 0:
            raise ContentHostError('There was an error installing katello-host-tools-tracer')
        self.execute('katello-tracer-upload')

    def register_to_cdn(self, pool_ids=[settings.subscription.rhn_poolid]):
        """Subscribe satellite to CDN"""
        self.remove_katello_ca()
        cmd_result = self.register_contenthost(
            org=None,
            lce=None,
            username=settings.subscription.rhn_username,
            password=settings.subscription.rhn_password,
        )
        if cmd_result.status != 0:
            raise ContentHostError(
                f'Error during registration, command output: {cmd_result.stdout}'
            )
        cmd_result = self.subscription_manager_attach_pool(pool_ids)[0]
        if cmd_result.status != 0:
            raise ContentHostError(
                f'Error during pool attachment, command output: {cmd_result.stdout}'
            )

    def ping_host(self, host):
        """Check the provisioned host status by pinging the ip of host

        :param host: IP address or hostname of the provisioned host
        :returns: None
        :raises: : `HostPingFailed` if the host is not pingable
        """
        result = self.execute(
            f'for i in {{1..60}}; do ping -c1 {host} && exit 0; sleep 20; done; exit 1'
        )
        if result.status != 0:
            raise HostPingFailed(f'Failed to ping host {host}:{result.stdout}')

    def update_host_location(self, location):
        host = self.nailgun_host.read()
        host.location = location
        host.update(['location'])


class Capsule(ContentHost, CapsuleMixins):
    rex_key_path = '~foreman-proxy/.ssh/id_rsa_foreman_proxy.pub'

    @property
    def nailgun_capsule(self):
        from nailgun.entities import Capsule as NailgunCapsule

        return NailgunCapsule().search(query={'search': f'name={self.hostname}'})[0]

    @cached_property
    def is_upstream(self):
        """Figure out which product distribution is installed on the server.

        :return: True if no downstream satellite RPMS are installed
        :rtype: bool
        """
        return self.execute('rpm -q satellite-capsule &>/dev/null').status != 0

    @cached_property
    def version(self):
        if not self.is_upstream:
            return self.execute('rpm -q satellite-capsule').stdout.split('-')[2]
        else:
            return 'upstream'

    @cached_property
    def url(self):
        return f'https://{self.hostname}'

    @cached_property
    def url_katello_ca_rpm(self):
        """Return the Katello cert RPM URL"""
        pub_url = urlunsplit(('http', self.hostname, 'pub/', '', ''))  # use url with https?
        return urljoin(pub_url, 'katello-ca-consumer-latest.noarch.rpm')

    @property
    def rex_pub_key(self):
        return self.execute(f'cat {self.rex_key_path}').stdout.strip()

    def restart_services(self):
        """Restart services, returning True if passed and stdout if not"""
        result = self.execute('satellite-maintain service restart')
        return True if result.status == 0 else result.stdout

    def check_services(self):
        error_msg = 'Some services are not running'
        result = self.execute('satellite-maintain service status')
        if result.status == 0:
            return True
        for line in result.stdout.splitlines():
            if error_msg in line:
                return line.replace(error_msg, '').strip()

    def install(self, installer_obj=None, cmd_args=None, cmd_kwargs=None):
        """General purpose installer"""
        if not installer_obj:
            command_opts = {'scenario': self.__class__.__name__.lower()}
            command_opts.update(cmd_kwargs)
            installer_obj = InstallerCommand(*cmd_args, **command_opts)
        return self.execute(installer_obj.get_command(), timeout=0)

    def get_features(self):
        """Get capsule features"""
        return requests.get(f'https://{self.hostname}:9090/features', verify=False).text

    def register_to_dogfood(self, ak_type='satellite'):
        dogfood_canonical_hostname = settings.repos.dogfood_repo_host.partition('//')[2]
        # get hostname of dogfood machine
        dig_result = self.execute(f'dig +short {dogfood_canonical_hostname}')
        # the host name finishes with a dot, so last character is removed
        dogfood_hostname = dig_result.stdout.split()[0][:-1]
        dogfood = Satellite(dogfood_hostname)
        self.install_katello_ca(satellite=dogfood)
        # satellite version consist from x.y.z, we need only x.y
        sat_release = '.'.join(self.version.split('.')[:2])
        cmd_result = self.register_contenthost(
            org=f'{settings.subscription.dogfood_org}',
            activation_key=f'{ak_type}-{sat_release}-qa-rhel{self.os_version.major}',
        )
        if cmd_result.status != 0:
            raise CapsuleHostError(
                f'Error during registration, command output: {cmd_result.stdout}'
            )

    def capsule_setup(self, sat_host=None, **installer_kwargs):
        """Prepare the host and run the capsule installer"""
        self._satellite = sat_host or Satellite()

        # Register capsule host to CDN and enable repos
        result = self.register_contenthost(
            org=None,
            lce=None,
            username=settings.subscription.rhn_username,
            password=settings.subscription.rhn_password,
            auto_attach=True,
        )
        if result.status:
            raise CapsuleHostError(f'Capsule CDN registration failed\n{result.stderr}')

        for repo in getattr(constants, f"OHSNAP_RHEL{self.os_version.major}_REPOS"):
            result = self.enable_repo(repo, force=True)
            if result.status:
                raise CapsuleHostError(f'Repo enable at capsule host failed\n{result.stdout}')

        # Update system, firewall services and check capsule is already installed from template
        self.execute('yum -y update', timeout=0)
        self.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
        self.execute('firewall-cmd --runtime-to-permanent')
        result = self.execute('rpm -q satellite-capsule')
        if result.status:
            raise CapsuleHostError(f'The satellite-capsule package was not found\n{result.stdout}')

        # Update Satellite's http proxy except list
        result = self.satellite.cli.Settings.list({'search': 'http_proxy_except_list'})[0]
        if result['value'] == '[]':
            except_list = f'[{self.hostname}]'
        else:
            except_list = result['value'][:-1] + f', {self.hostname}]'
        self.satellite.cli.Settings.set({'name': 'http_proxy_except_list', 'value': except_list})

        # Generate certificate, copy it to Capsule, run installer, check it succeeds
        installer = self.satellite.capsule_certs_generate(self, **installer_kwargs)
        self.satellite.session.remote_copy(installer.opts['certs-tar-file'], self)
        installer.update(**installer_kwargs)
        result = self.install(installer)
        if result.status:
            # before exit download the capsule log file
            self.session.sftp_read(
                '/var/log/foreman-installer/capsule.log',
                f'{settings.robottelo.tmp_dir}/capsule-{self.ip_addr}.log',
            )
            raise CapsuleHostError(
                f'Foreman installer failed at capsule host\n{result.stdout}\n{result.stderr}'
            )
        result = self.execute('satellite-maintain service status')
        if 'inactive (dead)' in '\n'.join(result.stdout):
            raise CapsuleHostError(
                f'A core service is not running at capsule host\n{result.stdout}'
            )

    @property
    def cli(self):
        """Import only satellite-maintain robottelo cli entities and wrap them under self.cli"""
        self._cli = type('cli', (), {'_configured': False})
        if self._cli._configured:
            return self._cli

        for file in Path('robottelo/cli/').iterdir():
            if (
                file.suffix == '.py'
                and not file.name.startswith('_')
                and file.name.startswith('sm_')
            ):
                cli_module = importlib.import_module(f'robottelo.cli.{file.stem}')
                for name, obj in cli_module.__dict__.items():
                    try:
                        if Base in obj.mro():
                            # create a copy of the class and set our hostname as a class attribute
                            new_cls = type(name, (obj,), {'hostname': self.hostname})
                            setattr(self._cli, name, new_cls)
                    except AttributeError:
                        # not everything has an mro method, we don't care about them
                        pass
        return self._cli


class Satellite(Capsule, SatelliteMixins):
    def __init__(self, hostname=None, **kwargs):
        from robottelo.config import settings

        hostname = hostname or settings.server.hostname  # instance attr set by broker.Host
        self.port = kwargs.get('port', settings.server.port)
        super().__init__(hostname=hostname, **kwargs)
        # create dummy classes for later population
        self._api = type('api', (), {'_configured': False})
        self._cli = type('cli', (), {'_configured': False})

    @property
    def api(self):
        """Import all nailgun entities and wrap them under self.api"""
        if not self._api:
            self._api = type('api', (), {'_configured': False})
        if self._api._configured:
            return self._api

        from nailgun.config import ServerConfig
        from nailgun.entity_mixins import Entity

        def inject_config(cls, server_config):
            """inject a nailgun server config into the init of nailgun entity classes"""
            import functools

            class DecClass(cls):
                __init__ = functools.partialmethod(cls.__init__, server_config=server_config)

            return DecClass

        # set the server configuration to point to this satellite
        self.nailgun_cfg = ServerConfig(
            auth=(settings.server.admin_username, settings.server.admin_password),
            url=f'{self.url}',
            verify=False,
        )
        # add each nailgun entity to self.api, injecting our server config
        for name, obj in entities.__dict__.items():
            try:
                if Entity in obj.mro():
                    #  create a copy of the class and inject our server config into the __init__
                    new_cls = type(name, (obj,), {})
                    setattr(self._api, name, inject_config(new_cls, self.nailgun_cfg))
            except AttributeError:
                # not everything has an mro method, we don't care about them
                pass
        return self._api

    @property
    def cli(self):
        """Import all robottelo cli entities and wrap them under self.cli"""
        if not self._cli:
            self._cli = type('cli', (), {'_configured': False})
        if self._cli._configured:
            return self._cli

        for file in Path('robottelo/cli/').iterdir():
            if file.suffix == '.py' and not file.name.startswith('_'):
                cli_module = importlib.import_module(f'robottelo.cli.{file.stem}')
                for name, obj in cli_module.__dict__.items():
                    try:
                        if Base in obj.mro():
                            # create a copy of the class and set our hostname as a class attribute
                            new_cls = type(name, (obj,), {'hostname': self.hostname})
                            setattr(self._cli, name, new_cls)
                    except AttributeError:
                        # not everything has an mro method, we don't care about them
                        pass
        return self._cli

    @property
    def internal_capsule(self):
        capsule_list = self.api.SmartProxy().search(query={'search': f'name={self.hostname}'})
        return None if not capsule_list else capsule_list[0]

    def ui_session(self, testname=None, user=None, password=None, url=None, login=True):
        """Initialize an airgun Session object and store it as self.ui_session"""

        from airgun.session import Session

        def get_caller():
            import inspect

            for frame in inspect.stack():
                if frame.function.startswith('test_'):
                    return frame.function

        return Session(
            session_name=testname or get_caller(),
            user=user or settings.server.admin_username,
            password=password or settings.server.admin_password,
            url=url,
            hostname=self.hostname,
            login=login,
        )

    @property
    def satellite(self):
        """Use self when no other Satellite is set to avoid unecessary/incorrect instances"""
        if not self._satellite:
            return self
        return self._satellite

    @cached_property
    def is_upstream(self):
        """Figure out which product distribution is installed on the server.

        :return: True if no downstream satellite RPMS are installed
        :rtype: bool
        """
        return self.execute('rpm -q satellite &>/dev/null').status != 0

    @cached_property
    def version(self):
        if not self.is_upstream:
            return self.execute('rpm -q satellite').stdout.split('-')[1]
        else:
            return 'upstream'

    def is_remote_db(self):
        return (
            self.execute(
                'grep "db_manage: false" /etc/foreman-installer/scenarios.d/satellite-answers.yaml'
            ).status
            == 0
        )

    def capsule_certs_generate(self, capsule, cert_path=None, **extra_kwargs):
        """Generate capsule certs, returning the cert path and the installer command args"""
        command = InstallerCommand(
            command='capsule-certs-generate',
            foreman_proxy_fqdn=capsule.hostname,
            certs_tar=cert_path or f'/root/{capsule.hostname}-certs.tar',
            **extra_kwargs,
        )
        result = self.execute(command.get_command())
        install_cmd = InstallerCommand.from_cmd_str(cmd_str=result.stdout)
        install_cmd.opts['certs-tar-file'] = f'/root/{capsule.hostname}-certs.tar'
        return install_cmd

    def __enter__(self):
        """Satellite objects can be used as a context manager to temporarily force everything
        to use the Satellite object's hostname.
        """
        self._revert = False
        # if the hostname is the same, don't make a change
        if self.hostname != settings.server.hostname:
            self._revert = True
            self._old_hostname = settings.server.hostname
            settings.server.hostname = self.hostname
            configure_nailgun()
            configure_airgun()
        return self

    def __exit__(self, *err_args):
        if self._revert:
            settings.server.hostname = self._old_hostname
            configure_nailgun()
            configure_airgun()

    def create_custom_environment(self, repo='generic_1'):
        """Download, install and import puppet module.
        Return the environment name where the puppet module is installed.
        This is workaround for 6.10, there is no longer content view.

        :param repo: custom puppet module repository
        :return: Puppet environment name,
            environment name is likely to be searched in next steps of the test
        """
        repo_name = CUSTOM_PUPPET_MODULE_REPOS[repo]
        if repo_name not in list(CUSTOM_PUPPET_MODULE_REPOS.values()):
            raise ValueError(
                f'Custom puppet module mismatch, actual custom puppet module repo: '
                f'"{repo_name}", does not match any available puppet module: '
                f'"{list(CUSTOM_PUPPET_MODULE_REPOS.values())}"'
            )
        env_name = gen_string('alpha')
        custom_puppet_module_repo = f'{repo_name}{CUSTOM_PUPPET_MODULE_REPOS_VERSION}'
        self.execute(
            f'curl -O {settings.robottelo.repos_hosting_url}{CUSTOM_PUPPET_MODULE_REPOS_PATH}'
            f'{custom_puppet_module_repo}',
        )
        self.execute(
            f'puppet module install {custom_puppet_module_repo} '
            f'--target-dir /etc/puppetlabs/code/environments/{env_name}/modules/'
        )
        smart_proxy = (
            self.api.SmartProxy().search(query={'search': f'name={self.hostname}'})[0].read()
        )
        smart_proxy.import_puppetclasses()
        return env_name

    def destroy_custom_environment(self, env_name):
        """Remove custom environment including installed modules."""
        self.execute(f'rm -rf /etc/puppetlabs/code/environments/{env_name}/')
        smart_proxy = (
            self.api.SmartProxy().search(query={'search': f'name={self.hostname}'})[0].read()
        )
        smart_proxy.import_puppetclasses()

    def delete_puppet_class(self, puppetclass_name):
        """Delete puppet class and its subclasses."""
        # Find puppet class
        puppet_classes = self.api.PuppetClass().search(
            query={'search': f'name = "{puppetclass_name}"'}
        )
        # And all subclasses
        puppet_classes.extend(
            self.api.PuppetClass().search(query={'search': f'name ~ "{puppetclass_name}::"'})
        )
        for puppet_class in puppet_classes:
            # Search and remove puppet class from affected hostgroups
            for hostgroup in puppet_class.read().hostgroup:
                hostgroup.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
            # Search and remove puppet class from affected hosts
            for host in self.api.Host().search(query={'search': f'class={puppet_class.name}'}):
                host.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
            # Remove puppet class entity
            puppet_class.delete()

    @contextmanager
    def hammer_api_timeout(self, timeout=-1):
        """Set hammer API request timeout on Satellite

        :param int timeout: request timeout in seconds
        """
        new_timeout = f':request_timeout: {timeout}'
        if self.execute(f"grep -i 'request_timeout' {HAMMER_CONFIG}").status != 0:
            self.execute(f"echo '  {new_timeout}' >> {HAMMER_CONFIG}")
            revert_method = 'remove'
        else:
            old_timeout = self.execute(f"sed -ne '/:request_timeout.*/p' {HAMMER_CONFIG}").stdout
            self.execute(f"sed -ir 's/{old_timeout.strip()}/{new_timeout}/' {HAMMER_CONFIG}")
            revert_method = 'replace'
        yield
        if revert_method == 'remove':
            self.execute(f"sed -i '/{new_timeout}/d' {HAMMER_CONFIG}")
        else:
            self.execute(f"sed -ie 's/{new_timeout}/{old_timeout.strip()}/' {HAMMER_CONFIG}")

    @contextmanager
    def skip_yum_update_during_provisioning(self, template=None):
        """Hides the yum update command with echo text

        :param str template: The template name where the yum update will be hidden
        """
        old = 'yum -t -y update'
        new = 'echo "Yum update skipped for faster automation testing"'
        update_provisioning_template(name=template, old=old, new=new)
        yield
        update_provisioning_template(name=template, old=new, new=old)

    def update_setting(self, name, value):
        """changes setting value and returns the setting value before the change."""
        setting = self.api.Setting().search(query={'search': f'name="{name}"'})[0]
        default_setting_value = setting.value
        if default_setting_value is None:
            default_setting_value = ''
        setting.value = value
        setting.update({'value'})
        return default_setting_value

    def install_cockpit(self):
        cmd_result = self.execute(
            'satellite-installer --no-colors --enable-foreman-plugin-remote-execution-cockpit',
            timeout='30m',
        )
        if cmd_result.status != 0:
            raise SatelliteHostError(
                f'Error during cockpit installation, installation output: {cmd_result.stdout}'
            )
        self.add_rex_key(self)

    def register_host_custom_repo(self, module_org, rhel_contenthost, repo_urls):
        """Register content host to Satellite and sync repos

        :param module_org: Org where contenthost will be registered.
        :param rhel_contenthost: contenthost to be register with Satellite.
        :param repo_urls: List of URLs to be synced and made available to contenthost
            via subscription-manager.
        :return: None
        """
        # Create a new product, sync appropriate client and other passed repos on satellite
        rhelver = rhel_contenthost.os_version.major
        prod = self.api.Product(
            organization=module_org, name=f'rhel{rhelver}_{gen_string("alpha")}'
        ).create()
        tasks = []
        for url in repo_urls:
            repo = self.api.Repository(
                organization=module_org,
                product=prod,
                content_type='yum',
                url=url,
            ).create()
            task = repo.sync(synchronous=False)
            tasks.append(task)
        for task in tasks:
            self.wait_for_tasks(
                search_query=(f'id = {task["id"]}'),
                poll_timeout=1500,
            )
            task_status = self.api.ForemanTask(id=task['id']).poll()
            assert task_status['result'] == 'success'
        subs = self.api.Subscription(organization=module_org, name=prod.name).search()
        assert len(subs), f'Subscription for sat client product: {prod.name} was not found.'
        subscription = subs[0]

        # register contenthost
        rhel_contenthost.install_katello_ca(self)
        register = rhel_contenthost.register_contenthost(
            org=module_org.label,
            lce='Library',
            name=f'{gen_string("alpha")}-{rhel_contenthost.hostname}',
            force=True,
        )
        assert register.status == 0, (
            f'Failed to register the host: {rhel_contenthost.hostname}:'
            f'rc: {register.status}: {register.stderr}'
        )
        # attach product subscriptions to contenthost
        rhel_contenthost.nailgun_host.bulk_add_subscriptions(
            data={
                "organization_id": module_org.id,
                "included": {"ids": [rhel_contenthost.nailgun_host.id]},
                "subscriptions": [{"id": subscription.id, "quantity": 1}],
            }
        )
        # refresh repository metadata on the host
        rhel_contenthost.execute('subscription-manager repos --list')


class SSOHost(Host):
    """Class for RHSSO functions and setup"""

    def __init__(self, sat_obj, **kwargs):
        self.satellite = sat_obj
        kwargs['hostname'] = kwargs.get('hostname', settings.rhsso.host_name)
        super().__init__(**kwargs)

    def get_rhsso_client_id(self):
        """getter method for fetching the client id and can be used other functions"""
        client_name = f'{self.satellite.hostname}-foreman-openidc'
        self.execute(
            f'{KEY_CLOAK_CLI} config credentials '
            f'--server {settings.rhsso.host_url.replace("https://", "http://")}/auth '
            f'--realm {settings.rhsso.realm} '
            f'--user {settings.rhsso.rhsso_user} '
            f'--password {settings.rhsso.rhsso_password}'
        )

        result = self.execute(f'{KEY_CLOAK_CLI} get clients --fields id,clientId')
        result_json = json.loads(result.stdout)
        client_id = None
        for client in result_json:
            if client_name in client['clientId']:
                client_id = client['id']
                break
        return client_id

    @lru_cache
    def get_rhsso_user_details(self, username):
        """Getter method to receive the user id"""
        result = self.execute(
            f"{KEY_CLOAK_CLI} get users -r {settings.rhsso.realm} -q username={username}"
        )
        result_json = json.loads(result.stdout)
        return result_json[0]

    @lru_cache
    def get_rhsso_groups_details(self, group_name):
        """Getter method to receive the group id"""
        result = self.execute(f"{KEY_CLOAK_CLI} get groups -r {settings.rhsso.realm}")
        group_list = json.loads(result.stdout)
        query_group = [group for group in group_list if group['name'] == group_name]
        return query_group[0]

    def upload_rhsso_entity(self, json_content, entity_name):
        """Helper method upload the entity json request as file on RHSSO Server"""
        with open(entity_name, "w") as file:
            json.dump(json_content, file)
        self.session.sftp_write(entity_name)

    def create_mapper(self, json_content, client_id):
        """Helper method to create the RH-SSO Client Mapper"""
        self.upload_rhsso_entity(json_content, "mapper_file")
        self.execute(
            f'{KEY_CLOAK_CLI} create clients/{client_id}/protocol-mappers/models -r '
            f'{settings.rhsso.realm} -f {"mapper_file"}'
        )

    def create_new_rhsso_user(self, username=None):
        """create new user in RHSSO instance and set the password"""
        update_data_user = Box(RHSSO_NEW_USER)
        update_data_pass = Box(RHSSO_RESET_PASSWORD)
        if not username:
            username = gen_string('alphanumeric')
        update_data_user.username = username
        update_data_user.email = username + random.choice(valid_emails_list())
        update_data_pass.value = settings.rhsso.rhsso_password
        self.upload_rhsso_entity(update_data_user, "create_user")
        self.upload_rhsso_entity(update_data_pass, "reset_password")
        self.execute(f"{KEY_CLOAK_CLI} create users -r {settings.rhsso.realm} -f create_user")
        user_details = self.get_rhsso_user_details(update_data_user.username)
        self.execute(
            f'{KEY_CLOAK_CLI} update -r {settings.rhsso.realm} '
            f'users/{user_details["id"]}/reset-password -f {"reset_password"}'
        )
        return update_data_user

    def update_rhsso_user(self, username, group_name=None):
        update_data_user = Box(RHSSO_USER_UPDATE)
        user_details = self.get_rhsso_user_details(username)
        update_data_user.realm = settings.rhsso.realm
        update_data_user.userId = f"{user_details['id']}"
        if group_name:
            group_details = self.get_rhsso_groups_details(group_name=group_name)
            update_data_user['groupId'] = f"{group_details['id']}"
            self.upload_rhsso_entity(update_data_user, "update_user")
            group_path = f"users/{user_details['id']}/groups/{group_details['id']}"
            self.execute(
                f"{KEY_CLOAK_CLI} update -r {settings.rhsso.realm} {group_path} -f update_user"
            )

    def delete_rhsso_user(self, username):
        """Delete the RHSSO user"""
        user_details = self.get_rhsso_user_details(username)
        self.execute(f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} users/{user_details['id']}")

    def create_group(self, group_name=None):
        """Create the RHSSO group"""
        update_user_group = Box(RHSSO_NEW_GROUP)
        if not group_name:
            group_name = gen_string('alphanumeric')
        update_user_group.name = group_name
        self.upload_rhsso_entity(update_user_group, "create_group")
        result = self.execute(
            f"{KEY_CLOAK_CLI} create groups -r {settings.rhsso.realm} -f create_group"
        )
        return result.stdout

    def delete_rhsso_group(self, group_name):
        """Delete the RHSSO group"""
        group_details = self.get_rhsso_groups_details(group_name)
        self.execute(
            f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} groups/{group_details['id']}"
        )

    def update_client_configuration(self, json_content):
        """Update the client configuration"""
        client_id = self.get_rhsso_client_id()
        self.upload_rhsso_entity(json_content, "update_client_info")
        update_cmd = (
            f"{KEY_CLOAK_CLI} update clients/{client_id}"
            "-f update_client_info -s enabled=true --merge"
        )
        self.execute(update_cmd)

    @cached_property
    def oidc_token_endpoint(self):
        """getter oidc token endpoint"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/token"
        )

    def get_oidc_client_id(self):
        """getter for the oidc client_id"""
        return f"{self.satellite.hostname}-foreman-openidc"

    @cached_property
    def oidc_authorization_endpoint(self):
        """getter for the oidc authorization endpoint"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/auth"
        )

    def get_two_factor_token_rh_sso_url(self):
        """getter for the two factor token rh_sso url"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/"
            f"auth?response_type=code&client_id={self.satellite.hostname}-foreman-openidc&"
            "redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=openid"
        )

    def set_the_redirect_uri(self):
        client_config = {
            "redirectUris": [
                "urn:ietf:wg:oauth:2.0:oob",
                f"https://{self.satellite.hostname}/users/extlogin/redirect_uri",
                f"https://{self.satellite.hostname}/users/extlogin",
            ]
        }
        self.update_client_configuration(client_config)
