"""Virtual machine client provisioning with satellite capsule product setup"""
import logging
import time

import os
from fauxfactory import gen_alphanumeric

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL7,
    SATELLITE_FIREWALL_SERVICE_NAME,
)
from robottelo.decorators import setting_is_set
from robottelo.cli.capsule import Capsule
from robottelo.cli.host import Host
from robottelo.helpers import extract_capsule_satellite_installer_command
from robottelo.ssh import download_file, upload_file
from robottelo.vm import VirtualMachine
from tempfile import mkstemp

logger = logging.getLogger(__name__)


class CapsuleVirtualMachineError(Exception):
    """Exception raised for failed capsule virtual machine operations"""


class CapsuleVirtualMachine(VirtualMachine):
    """Virtual machine client provisioning with satellite capsule product
    setup
    """

    def __init__(
            self, cpu=4, ram=16384, distro=None, provisioning_server=None,
            image_dir=None, org_id=None, lce_id=None,
            organization_ids=None, location_ids=None):
        """Manage a virtual machine with satellite capsule product setup for
        client provisioning.

        :param int cpu: The number of CPUs usage.
        :param int ram: the number of RAM usage in mega bytes.
        :param str distro: The OS distro to use to provision the virtual
         machine, it's also used in capsule setup to prepare the satellite
         products content.
        :param str provisioning_server: the provisioning server url
        :param str image_dir: the images location path on the provisioning
         server.
        :param int org_id: The organization id used to subscribe the
         virtual machine and to create the products contents that the virtual
         machine will use to setup the capsule.
        :param int lce_id: the lifecycle environment used for the subscription
         of virtual machine
        :param List[int] organization_ids: the organization ids of
         organizations that will use the capsule.
        :param List[int] location_ids: the location ids for which the content
         will be synchronized.
        """
        # ensure that capsule configuration exist and validate
        if not setting_is_set('capsule'):
            raise CapsuleVirtualMachineError('capsule configuration not set')

        name_prefix = gen_alphanumeric(4).lower()
        self._capsule_instance_name = (
            '{0}-{1}'.format(name_prefix, settings.capsule.instance_name)
        )
        self._capsule_domain = settings.clients.provisioning_server.split(
            '.', 1)[1]
        self._capsule_hostname = (
            '{0}.{1}'.format(
                self._capsule_instance_name,
                self._capsule_domain
            )
        )

        super(CapsuleVirtualMachine, self).__init__(
            cpu=cpu, ram=ram, distro=distro,
            provisioning_server=provisioning_server, image_dir=image_dir,
            domain=self._capsule_domain,
            hostname=self._capsule_hostname,
            target_image=self._capsule_instance_name
        )

        self._capsule_org_id = org_id
        self._capsule_lce_id = lce_id
        if organization_ids is None:
            organization_ids = []
        self._capsule_organization_ids = organization_ids
        if location_ids is None:
            location_ids = []
        self._capsule_location_ids = location_ids
        self._capsule = None
        self._capsule_org = None
        self._capsule_lce = None

    @property
    def hostname_local(self):
        """The virtual machine local hostname from provisioning server"""
        return '{0}.local'.format(self._target_image)

    @property
    def capsule_org(self):
        return self._capsule_org

    @property
    def capsule(self):
        return self._capsule

    @property
    def capsule_lce(self):
        return self._capsule_lce

    @property
    def capsule_location_ids(self):
        return self._capsule_location_ids

    @property
    def capsule_organization_ids(self):
        return self._capsule_organization_ids

    def _capsule_setup_name_resolution(self):
        """Setup a name resolution so the capsule and satellite
        are resolvable
        """
        self.run('echo "{0} {1} {2}" >> /etc/hosts'.format(
            self.ip_addr, self._capsule_hostname, self._capsule_instance_name))

        # add the capsule reverse record to the satellite hosts file
        ssh.command(
            u'sed -i \'/{0}/d\' /etc/hosts &&'
            u' echo "{1} {0}" >> /etc/hosts'
            .format(self._capsule_hostname, self.ip_addr),
            hostname=settings.server.hostname
        )
        if self.distro[:-1] == DISTRO_RHEL7:
            self.run('hostnamectl set-hostname {}'.format(
                self._capsule_hostname))

        def ensure_host_resolved(
                ssh_func, host_to_ping, ip_addr, time_sleep=60, retries=10):
            resolved = False
            retry_max_index = retries - 1
            for retry_index in range(retries):
                ssh_func_result = ssh_func('ping -c 1 {}'.format(host_to_ping))
                ssh_func_output = ''.join(ssh_func_result.stdout)
                if ssh_func_result.return_code == 0 and (
                        '({})'.format(ip_addr) in ssh_func_output):
                    resolved = True
                    break

                if retry_index != retry_max_index:
                    # do not sleep at last index
                    time.sleep(time_sleep)

            return resolved

        # Ensure capsule hostname is resolvable from the server host
        hostname_resolved = ensure_host_resolved(
            ssh.command, self._capsule_hostname, self.ip_addr)
        if not hostname_resolved:
            raise CapsuleVirtualMachineError(
                'Failed to resolve the capsule hostname from the server')

        # Ensure capsule hostname is resolvable at capsule host
        '''hostname_resolved = ensure_host_resolved(
            self.run, self._capsule_hostname, '127.0.0.1', retries=1)
        if not hostname_resolved:
            raise CapsuleVirtualMachineError(
                'Failed to resolver the capsule hostname from capsule')
        '''

        if self.distro[:-1] == DISTRO_RHEL7:
            # Add RH-Satellite-6 service to firewall public zone
            self.run('firewall-cmd --zone=public --add-service={}'.format(
                SATELLITE_FIREWALL_SERVICE_NAME))

    def _capsule_cleanup(self):
        """make the necessary cleanup in case of a crash"""
        if self._subscribed:
            # use try except to unregister the host, in case of host not
            # reachable (or any other failure), the capsule is not deleted and
            # this failure will hide any prior failure.
            try:
                self.unregister()
            except Exception as exp:
                logger.error('Failed to unregister the host: {0}\n{1}'.format(
                    self.hostname, exp))

        if self._capsule_hostname:
            # do cleanup as using a static hostname that can be reused by
            # other tests and organizations
            try:
                # try to delete the hostname first
                Host.delete({'name': self._capsule_hostname})
                # try delete the capsule
            except Exception as exp:
                # log the exception
                # as maybe that the host was not registered or setup does not
                # reach that stage
                # or maybe that the capsule was not registered or setup does
                # not reach that stage
                # Destroys the Capsule VM on the provisioning server if
                # exception has 'return_code=70(Error: host not found)'
                if exp.return_code == 70:
                    super(CapsuleVirtualMachine, self).destroy()

                # BEGIN BZ:1622064
                logger.warn('Failed to cleanup the host: {0}\n{1}'.format(
                    self.hostname, exp))
                # when BZ is closed the exception should `raise` here.
                # END BZ:1622064

            try:
                # try to delete the capsule if it was added already
                Capsule.delete({'name': self._capsule_hostname})
            except Exception as exp:
                logger.error('Failed to cleanup the capsule: {0}\n{1}'.format(
                    self.hostname, exp))
                raise

    def _setup_capsule(self):
        """Prepare the virtual machine to host a capsule node"""
        # setup the name resolution
        self._capsule_setup_name_resolution()
        logger.info('adding repofiles required for capsule installation')
        self.create_custom_repos(
            capsule=settings.capsule_repo,
            rhscl=settings.rhscl_repo,
            ansible=settings.ansible_repo,
            maint=settings.satmaintenance_repo
        )
        self.configure_rhel_repo(settings.__dict__[self.distro[:-1] + '_repo'])
        self.run('yum repolist')
        self.run('yum -y install satellite-capsule', timeout=1200)
        result = self.run('rpm -q satellite-capsule')
        if result.return_code != 0:
            raise CapsuleVirtualMachineError(
                u'Failed to install satellite-capsule package\n{}'.format(
                    result.stderr)
            )
        cert_file_path = '/root/{0}-certs.tar'.format(self.hostname)
        certs_gen = ssh.command(
            'capsule-certs-generate '
            '--foreman-proxy-fqdn {0} '
            '--certs-tar {1}'
            .format(self.hostname, cert_file_path)
        )
        if certs_gen.return_code != 0:
            raise CapsuleVirtualMachineError(
                u'Unable to generate certificate\n{}'
                .format(certs_gen.stderr)
            )
        # copy the certificate to capsule vm
        _, temporary_local_cert_file_path = mkstemp(suffix='-certs.tar')
        logger.info(
            'downloading the certs file: {0}'.format(cert_file_path)
        )
        download_file(
            remote_file=cert_file_path,
            local_file=temporary_local_cert_file_path,
            hostname=settings.server.hostname
        )
        logger.info(
            'uploading the certs file: {0}'.format(cert_file_path)
        )
        upload_file(
            key_filename=settings.server.ssh_key,
            local_file=temporary_local_cert_file_path,
            remote_file=cert_file_path,
            hostname=self.ip_addr
        )
        # delete the temporary file
        os.remove(temporary_local_cert_file_path)

        installer_cmd = extract_capsule_satellite_installer_command(
                            certs_gen.stdout
                        )
        result = self.run(installer_cmd, timeout=1800)
        if result.return_code != 0:
            # before exit download the capsule log file
            _, log_path = mkstemp(prefix='capsule_external-', suffix='.log')
            download_file(
                '/var/log/foreman-installer/capsule.log',
                log_path,
                self.ip_addr
            )
            raise CapsuleVirtualMachineError(
                result.return_code, result.stderr,
                u'foreman installer failed at capsule host')

        # manually start pulp_celerybeat service if BZ1446930 is open
        result = self.run('systemctl status pulp_celerybeat.service')
        if 'inactive (dead)' in '\n'.join(result.stdout):
            # BEGIN BZ:1446930
            result = self.run('systemctl start pulp_celerybeat.service')
            if result.return_code != 0:
                raise CapsuleVirtualMachineError(
                    'Failed to start pulp_celerybeat service\n{}'.format(
                        result.stderr)
                )
            # When BZ is fixed the above can be replaced with the below.
            # raise CapsuleVirtualMachineError(
            #     'pulp_celerybeat service not running')
            # END BZ:1446930

    def create(self):
        super(CapsuleVirtualMachine, self).create()
        try:
            self._setup_capsule()
        except Exception:
            # handle exception as VirtualMachine has no exception handling
            # in __enter__ function
            self.destroy()
            raise

    def suspend(self, ensure=False, timeout=None, connection_timeout=30):
        """Suspend the virtual machine.

        :param bool ensure: ensure that the virtual machine is unreachable
        :param int timeout: Time to wait for the ssh command to finish.
        :param int connection_timeout: Time to wait for establishing the
            connection.

        Notes:

        1. The virtual machine will consume system RAM but not processor
           resources. Disk and network I/O does not occur while the guest is
           suspended.
        2. This operation is immediate and the guest can be restarted with
           resume.
        """
        result = ssh.command(
            u'virsh suspend {0}'.format(self._target_image),
            hostname=self.provisioning_server,
            timeout=timeout,
            connection_timeout=connection_timeout,
        )
        suspended = True if result.return_code == 0 else False
        if suspended and ensure:
            # ping one time the virtual machine to ensure that it's unreachable
            result = ssh.command(
                'ping -c 1 {}'.format(self.hostname),
                hostname=self.provisioning_server,
                connection_timeout=connection_timeout
            )
            suspended = True if result.return_code != 0 else False

        return suspended

    def resume(self, ensure=False, timeout=None, connection_timeout=30):
        """Restore from a suspended state

        :param bool ensure: ensure that the virtual machine is reachable
        :param int timeout: Time to wait for the ssh command to finish.
        :param int connection_timeout: Time to wait for establishing the
            connection.

        Note: This operation is immediate
        """
        result = ssh.command(
            u'virsh resume {0}'.format(self._target_image),
            hostname=self.provisioning_server,
            timeout=timeout,
            connection_timeout=connection_timeout,
        )
        resumed = True if result.return_code == 0 else False
        if resumed and ensure:
            # ping one time the virtual machine to ensure that it's reachable
            result = ssh.command(
                'ping -c 1 {}'.format(self.ip_addr),
                hostname=self.provisioning_server,
                connection_timeout=connection_timeout,
            )
            resumed = True if result.return_code == 0 else False

        return resumed

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        self._capsule_cleanup()
        super(CapsuleVirtualMachine, self).destroy()
