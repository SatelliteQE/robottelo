import re
import time
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlunsplit

from broker import VMBroker
from broker.hosts import Host
from fauxfactory import gen_alpha
from fauxfactory import gen_string
from nailgun import entities
from packaging.version import Version
from wait_for import TimedOutError
from wait_for import wait_for
from wrapanapi.entities.vm import VmState

from robottelo import constants
from robottelo.api.utils import update_provisioning_template
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_job_invocation
from robottelo.cli.job_invocation import JobInvocation
from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import settings
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS_PATH
from robottelo.constants import CUSTOM_PUPPET_MODULE_REPOS_VERSION
from robottelo.constants import HAMMER_CONFIG
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.helpers import get_data_file
from robottelo.helpers import InstallerCommand


POWER_OPERATIONS = {
    VmState.RUNNING: 'running',
    VmState.STOPPED: 'stopped',
    'reboot': 'reboot'
    # TODO paused, suspended, shelved?
}


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


class ContentHost(Host):
    run = Host.execute

    def __init__(self, hostname, auth=None, **kwargs):
        """ContentHost object with optional ssh connection

        :param hostname: The fqdn of a ContentHost target
        :param auth: ('root', 'rootpass') or '/path/to/keyfile.rsa'
        """
        if not hostname:
            raise ContentHostError('A valid hostname must be provided')
        if isinstance(auth, tuple):
            # username/password-based auth
            kwargs.update({'username': auth[0], 'password': auth[1]})
        elif isinstance(auth, str):
            # key file based authentication
            kwargs.update({'key_filename': auth})
        super().__init__(hostname=hostname, **kwargs)

    @property
    def nailgun_host(self):
        """If this host is subscribed, provide access to its nailgun object"""
        if self.subscribed:
            return entities.Host().search(query={'search': self.hostname})[0]

    @property
    def subscribed(self):
        """Boolean representation of a content host's subscription status"""
        return 'Status: Unknown' not in self.execute('subscription-manager status').stdout

    @property
    def ip_addr(self):
        ipv4, ipv6 = self.execute('hostname -I').stdout.split()
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
        self.remove_katello_ca()
        self.execute('subscription-manager clean')

    def teardown(self):
        self.unregister()

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
            VMBroker()
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
            self.execute(f'subscription-manager repos --enable {repo}')

    def subscription_manager_list_repos(self):
        return self.execute('subscription-manager repos --list')

    def subscription_manager_status(self):
        return self.execute('subscription-manager status')

    def subscription_manager_list(self):
        return self.execute('subscription-manager list')

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

    def install_katello_agent(self):
        """Install katello-agent on the virtual machine.

        :return: None.
        :raises ContentHostError: if katello-agent is not installed.
        """
        result = self.execute('yum install -y katello-agent')
        if result.status != 0:
            raise ContentHostError(f'Failed to install katello-agent: {result.stdout}')
        try:
            wait_for(lambda: self.execute('systemctl status goferd').status == 0)
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
        self.execute(f'rpm -Uvh {satellite.url_katello_ca_rpm}')
        # Not checking the return_code here, as rpm could be installed before
        # and installation may fail
        result = self.execute(f'rpm -q katello-ca-consumer-{satellite.hostname}')
        # Checking the return_code here to verify katello-ca rpm is actually
        # present in the system
        if result.status != 0:
            ContentHostError('Failed to download and install the katello-ca rpm')

    def remove_katello_ca(self):
        """Removes katello-ca rpm from the broker virtual machine.

        :return: None.
        :raises robottelo.hosts.ContentHostError: If katello-ca wasn't removed.
        """
        # Not checking the return_code here, as rpm can be not even installed
        # and deleting may fail
        self.execute('yum erase -y $(rpm -qa |grep katello-ca-consumer)')
        # Checking the return_code here to verify katello-ca rpm is actually
        # not present in the system
        result = self.execute('rpm -qa |grep katello-ca-consumer')
        if result.status == 0:
            raise ContentHostError(f'katello-ca rpm(s) are still installed: {result.stdout}')
        self.execute('subscription-manager clean')

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

    def register_contenthost(
        self,
        org='Default_Organization',
        activation_key=None,
        lce='Library',
        consumerid=None,
        force=True,
        releasever=None,
        username=None,
        password=None,
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

            cmd += f' --consumerid {consumerid} --username {username} --password {password}'
            if auto_attach:
                cmd += ' --auto-attach'
        else:
            raise ContentHostError(
                'Please provide either activation key or lifecycle '
                'environment name to successfully register a host'
            )
        if releasever is not None:
            cmd += f' --release {releasever}'
        if force:
            cmd += ' --force'
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
        """Put a local file to the broker virtual machine."""
        self.session.sftp_write(source=local_path, destination=remote_path)

    def put_ssh_key(self, source_key_path, destination_key_name):
        """Copy ssh key to virtual machine ssh path and ensure proper permission is
        set

        :param source_key_path: The ssh key file path to copy to vm
        :param destination_key_name: The ssh key file name when copied to vm
        """
        destination_key_path = f'/root/.ssh/{destination_key_name}'
        self.put(local_path=source_key_path, remote_path=destination_key_path)
        result = self.run(f'chmod 600 {destination_key_path}')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to chmod ssh key file:\n{result.stderr}')

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
        result = self.run(f'touch {ssh_config_file_path}')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to create ssh config file:\n{result.stderr}')
        result = self.run(
            f'echo "\nHost {host}\n\tHostname {host}\n\tUser {user}\n'
            f'\tIdentityFile {ssh_key_file_path}\n" >> {ssh_config_file_path}'
        )
        if result.status != 0:
            raise CLIFactoryError(f'Failed to write to ssh config file:\n{result.stderr}')
        # add host entry to ssh known_hosts
        result = self.run(f'ssh-keyscan {host} >> {ssh_path}/known_hosts')
        if result.status != 0:
            raise CLIFactoryError(
                f'Failed to put hostname in ssh known_hosts files:\n{result.stderr}'
            )

    def configure_rhel_repo(self, rhel_repo):
        """Configures specified Red Hat repository on the broker virtual machine.

        :param rhel_repo: Red Hat repository link from properties file.
        :return: None.

        """
        self.execute(f'curl -o /etc/yum.repos.d/rhel.repo {rhel_repo}')

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
        result = self.execute('yum install puppet -y')
        if result.status != 0:
            raise ContentHostError('Failed to install the puppet rpm')
        self.execute(f'echo "{puppet_conf}" >> /etc/puppetlabs/puppet/puppet.conf')
        # This particular puppet run on client would populate a cert on
        # sat6 under the capsule --> certifcates or on capsule via cli "puppetserver
        # ca list", so that we sign it.
        self.execute('puppet agent -t')
        proxy_host = Host(proxy_hostname)
        proxy_host.execute(cmd='puppetserver ca sign --all')
        # This particular puppet run would create the host entity under
        # 'All Hosts' and let's redirect stderr to /dev/null as errors at
        #  this stage can be ignored.
        self.execute('puppet agent -t 2> /dev/null')

    def job_invocation(self, job_template):
        """
        Invoke a job on the host.
        Args:
            job-template: name of job-templete to be used.

        Returns:

        """
        invocation_command = make_job_invocation(
            {'job-template': job_template, 'search-query': f"name ~ {self.hostname}"}
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': self.hostname}
                    )
                )
            )
            data = self.execute(
                'rpm -qa |grep scap; yum repolist;cat /etc/foreman_scap_client/config.yaml; '
                'cat /etc/cron.d/foreman_scap_client_cron;tail -n 100 /var/log/messages'
            )
            raise AssertionError(
                f'Failed to execute foreman_scap_client run. '
                f'host_data_stdout: {data.stdout}, and host_data_stderr: {data.stderr}'
                f'job_invocation: {result}'
            )

    def execute_foreman_scap_client(self, policy_id=None):
        """Executes foreman_scap_client on the vm to create security audit report.

        :param policy_id: The Id of the OSCAP policy.
        :return: None.

        """
        if policy_id is None:
            result = self.execute(
                'awk -F "/" \'/download_path/ {print $4}\' /etc/foreman_scap_client/config.yaml'
            )
            policy_id = result.stdout[0]
        result = self.execute(f'foreman_scap_client ds {policy_id}')
        if result.status != 0:
            data = self.execute(
                'rpm -qa |grep scap; yum repolist;cat /etc/foreman_scap_client/config.yaml; '
                'cat /etc/cron.d/foreman_scap_client_cron; tail -n 100 /var/log/messages'
            )
            raise ContentHostError(
                f'Failed to execute foreman_scap_client run. '
                f'Command exited with code: {result.status}, stderr: {result.stderr}, stdout: {result.stdout}'
                f'host_data_stdout: {data.stdout}, and host_data_stderr: {data.stderr}'
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
        add_remote_execution_ssh_key(self.ip_addr, proxy_hostname=satellite.hostname)
        if register and subnet_id is not None:
            host = self.nailgun_host.read()
            host.name = self.hostname
            host.subnet_id = int(subnet_id)
            host.update(['name', 'subnet_id'])
        if register and by_ip:
            # connect to host by ip
            host = self.nailgun_host.read()
            host_parameters = [{'name': 'remote_execution_connect_by_ip', 'value': 'True'}]
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
            constants.DISTRO_RHEL6: settings.repos.rhel6_repo,
            constants.DISTRO_RHEL7: settings.repos.rhel7_repo,
            constants.DISTRO_RHEL8: settings.repos.rhel8_repo,
        }
        rhel_repo = distro_repo_map.get(rhel_distro)

        if rhel_repo is None:
            raise ContentHostError(f'Missing RHEL repository configuration for {rhel_distro}.')

        self.configure_rhel_repo(rhel_repo)

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
        self.install_katello_ca(satellite)
        self.register_contenthost(org_label, activation_key=activation_key, lce=lce)
        if not self.subscribed:
            raise CLIFactoryError('Virtual machine failed subscription')
        if patch_os_release_distro:
            self.patch_os_release_version(distro=patch_os_release_distro)
        # Enable RH repositories
        for repo_id in rh_repo_ids:
            self.enable_repo(repo_id, force=True)
        if product_label:
            # Enable custom repositories
            for repo_label in repo_labels:
                result = self.run(
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
        self.configure_rhel_repo(rhel_repo_url)
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
        self.run(f'mkdir -p {virt_who_deploy_directory}')
        # create the virt-who directory on satellite
        satellite = Satellite()
        satellite.execute(f'mkdir -p {virt_who_deploy_directory}')
        VirtWhoConfig.fetch({'id': config_id, 'output': virt_who_deploy_file})
        # remote_copy from satellite to self
        satellite.session.remote_copy(virt_who_deploy_file, self)

        # ensure the virt-who config deploy script is executable
        result = self.run(f'chmod +x {virt_who_deploy_file}')
        if result.status != 0:
            raise CLIFactoryError(
                f'Failed to set deployment script as executable:\n{result.stderr}'
            )
        # execute the deployment script
        result = self.run(f'{virt_who_deploy_file}')
        if result.status != 0:
            raise CLIFactoryError(f'Deployment script failure:\n{result.stderr}')
        # after this step, we should have virt-who service installed and started
        if exec_one_shot:
            # usually to be sure that the virt-who generated the report we need
            # to force a one shot report, for this we have to stop the virt-who
            # service
            result = self.run('service virt-who stop')
            if result.status != 0:
                raise CLIFactoryError(f'Failed to stop the virt-who service:\n{result.stderr}')
            result = self.run('virt-who --one-shot', timeout=900)
            if result.status != 0:
                raise CLIFactoryError(
                    f'Failed when executing virt-who --one-shot:\n{result.stderr}'
                )
            result = self.run('service virt-who start')
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
            self.session.sftp_write(get_data_file(file), f'/root/{file}')
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


class Capsule(ContentHost):
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
        return self.execute('rpm -q satellite &>/dev/null').status != 0

    @cached_property
    def url(self):
        return f'https://{self.hostname}'

    def restart_services(self):
        """Restart services, returning True if passed and stdout if not"""
        result = self.execute('foreman-maintain service restart')
        return True if result.status == 0 else result.stdout

    def check_services(self):
        error_msg = 'Some services are not running'
        result = self.execute('foreman-maintain service status')
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
        return self.execute(installer_obj.get_command())

    def capsule_setup(self, sat_host=None, **installer_kwargs):
        """Prepare the host and run the capsule installer"""
        self.satellite = sat_host or Satellite()
        self.create_custom_repos(
            capsule=settings.repos.capsule_repo,
            rhscl=settings.repos.rhscl_repo,
            ansible=settings.repos.ansible_repo,
            maint=settings.repos.satmaintenance_repo,
        )
        self.configure_rhel_repo(settings.repos.rhel7_repo)
        # self.execute('yum repolist')
        self.execute('yum -y update')
        self.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
        self.execute('firewall-cmd --runtime-to-permanent')
        # self.execute('yum -y install satellite-capsule', timeout=1200)
        result = self.execute('rpm -q satellite-capsule')
        if result.status != 0:
            raise CapsuleHostError(f'Failed to install satellite-capsule package\n{result.stderr}')
        # update http proxy except list
        result = self.satellite.cli.Settings.list({'search': 'http_proxy_except_list'})[0]
        if result['value'] == '[]':
            except_list = f'[{self.hostname}]'
        else:
            except_list = result['value'][:-1] + f', {self.hostname}]'
        result = self.satellite.cli.Settings.set(
            {'name': 'http_proxy_except_list', 'value': except_list}
        )
        # generate certificate
        installer = self.satellite.capsule_certs_generate(self, **installer_kwargs)
        # copy certs from satellite to capsule
        self.satellite.session.remote_copy(installer.opts['certs-tar-file'], self)
        installer.update(**installer_kwargs)
        result = self.install(installer)
        if result.status != 0:
            # before exit download the capsule log file
            self.session.sftp_read(
                '/var/log/foreman-installer/capsule.log',
                f'{settings.robottelo.tmp_dir}/capsule-{self.ip_addr}.log',
            )
            raise CapsuleHostError(f'foreman installer failed at capsule host: {result.stderr}')
        result = self.execute('systemctl status pulp_celerybeat.service')
        if 'inactive (dead)' in '\n'.join(result.stdout):
            raise CapsuleHostError('pulp_celerybeat service not running')


class Satellite(Capsule):
    def __init__(self, hostname=None, **kwargs):
        from robottelo.config import settings

        hostname = hostname or settings.server.hostname  # instance attr set by broker.Host
        self.port = kwargs.get('port', settings.server.port)
        super().__init__(hostname=hostname, **kwargs)
        # create dummy classes for later population
        self._api = type('api', (), {'_configured': False})
        self._cli = type('cli', (), {'_configured': False})
        self._ui_session = None

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
                    setattr(self._api, name, inject_config(obj, self.nailgun_cfg))
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

        import importlib
        from robottelo.cli.base import Base

        for file in Path('robottelo/cli/').iterdir():
            if file.suffix == '.py' and not file.name.startswith('_'):
                cli_module = importlib.import_module(f'robottelo.cli.{file.stem}')
                for name, obj in cli_module.__dict__.items():
                    try:
                        if Base in obj.mro():
                            # set our hostname as a class attribute
                            obj.hostname = self.hostname
                            setattr(self._cli, name, obj)
                    except AttributeError:
                        # not everything has an mro method, we don't care about them
                        pass
        return self._cli

    @property
    def ui_session(self):
        """Initialize an airgun Session object and store it as self.ui_session"""
        if self._ui_session:
            return self._ui_session

        from airgun.session import Session

        def get_caller():
            import inspect

            for frame in inspect.stack():
                if frame.function.startswith('test_'):
                    return frame.function

        self._ui_session = Session(
            session_name=get_caller(),
            user=settings.server.admin_username,
            password=settings.server.admin_password,
            hostname=self.hostname,
        )
        return self._ui_session

    @cached_property
    def version(self):
        if not self.is_upstream:
            return self.execute('rpm -q satellite').stdout.split('-')[1]
        else:
            return 'upstream'

    @cached_property
    def url_katello_ca_rpm(self):
        """Return the Katello cert RPM URL"""
        pub_url = urlunsplit(('http', self.hostname, 'pub/', '', ''))  # use url with https?
        return urljoin(pub_url, 'katello-ca-consumer-latest.noarch.rpm')

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
            entities.SmartProxy()
            .search(query={'search': f'name={settings.server.hostname}'})[0]
            .read()
        )
        smart_proxy.import_puppetclasses()
        return env_name

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
