"""Virtual machine client provisioning with satellite capsule product setup"""
import logging
import time

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    SATELLITE_FIREWALL_SERVICE_NAME,
)
from robottelo.cli.capsule import Capsule
from robottelo.cli.factory import (
    setup_capsule_virtual_machine,
)
from robottelo.cli.host import Host
from robottelo.decorators import setting_is_set
from robottelo.host_info import get_host_os_version
from robottelo.vm import VirtualMachine

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

        if distro is None:
            # use the same distro as satellite host server os
            server_host_os_version = get_host_os_version()
            if server_host_os_version.startswith('RHEL6'):
                distro = DISTRO_RHEL6
            elif server_host_os_version.startswith('RHEL7'):
                distro = DISTRO_RHEL7
            else:
                raise CapsuleVirtualMachineError(
                    'cannot find a default compatible distro to create'
                    ' the virtual machine')

        self._capsule_distro = distro
        self._capsule_domain = settings.capsule.domain
        self._capsule_instance_name = settings.capsule.instance_name
        self._capsule_hostname_hash = settings.capsule.hash
        self._capsule_hostname = settings.capsule.hostname
        self._ddns_package_url = settings.capsule.ddns_package_url

        super(CapsuleVirtualMachine, self).__init__(
            cpu=cpu, ram=ram, distro=distro,
            provisioning_server=provisioning_server, image_dir=image_dir,
            hostname=self._capsule_hostname,
            domain=self._capsule_domain,
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
    def capsule_distro(self):
        return self._capsule_distro

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

    def _capsule_setup_ddns(self):
        """Setup and configure ddns client and ensure it's functionality"""
        self.run('yum localinstall -y {}'.format(self._ddns_package_url))
        ddns_package_prefix = 'redhat-internal-ddns'
        ddns_bin_client = '{0}-client.sh'.format(ddns_package_prefix)
        ddns_bin_client_support_update = True
        if ddns_package_prefix not in self._ddns_package_url:
            ddns_package_prefix = 'redhat-ddns'
            ddns_bin_client = '{0}-client'.format(ddns_package_prefix)
            ddns_bin_client_support_update = False

        self.run(
            'echo "{0} {1} {2}" >> /etc/{3}/hosts'.format(
                self._capsule_instance_name,
                self._capsule_domain,
                self._capsule_hostname_hash,
                ddns_package_prefix
            )
        )
        self.run('echo "127.0.0.1 {} localhost" > /etc/hosts'.format(
            self._capsule_hostname))
        self.run('echo "{0} {1} {2}" >> /etc/hosts'.format(
            self.ip_addr, self._capsule_hostname, self._capsule_instance_name))

        if self.capsule_distro == DISTRO_RHEL7:
            self.run('hostnamectl set-hostname {}'.format(
                self._capsule_hostname))

        self.run('{0} enable'.format(ddns_bin_client))
        if ddns_bin_client_support_update:
            self.run('{0} update'.format(ddns_bin_client))

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
                'Failed to resolver the capsule hostname from the server')

        # Ensure capsule hostname is resolvable at capsule host
        hostname_resolved = ensure_host_resolved(
            self.run, self._capsule_hostname, '127.0.0.1', retries=1)
        if not hostname_resolved:
            raise CapsuleVirtualMachineError(
                'Failed to resolver the capsule hostname from capsule')

        if self.capsule_distro == DISTRO_RHEL7:
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
                # note: if the host was not registered the capsule does not
                # exist yet
                Capsule.delete({'name': self._capsule_hostname})
            except Exception as exp:
                # do nothing, only log the exception
                # as maybe that the host was not registered or setup does not
                # reach that stage
                # or maybe that the capsule was not registered or setup does
                # not reach that stage
                logger.error('Failed to cleanup the host: {0}\n{1}'.format(
                    self.hostname, exp))

    def _setup_capsule(self):
        """Prepare the virtual machine to host a capsule node"""
        # setup the ddns client to have a resolvable capsule hostname
        self._capsule_setup_ddns()

        setup_result = setup_capsule_virtual_machine(
            self,
            org_id=self._capsule_org_id,
            lce_id=self._capsule_lce_id,
            organization_ids=self._capsule_organization_ids,
            location_ids=self._capsule_location_ids
        )

        self._capsule, self._capsule_org, self._capsule_lce = setup_result

        self._capsule_org_id = self._capsule_org['id']
        self._capsule_lce_id = self._capsule_lce['id']

    def create(self):
        super(CapsuleVirtualMachine, self).create()
        try:
            self._setup_capsule()
        except Exception:
            # handle exception as VirtualMachine has no exception handling
            # in __enter__ function
            self._capsule_cleanup()
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
                'ping -c 1 {}'.format(self.hostname),
                hostname=self.provisioning_server,
                connection_timeout=connection_timeout,
            )
            resumed = True if result.return_code == 0 else False

        return resumed

    def destroy(self):
        """Destroys the virtual machine on the provisioning server"""
        self._capsule_cleanup()
        super(CapsuleVirtualMachine, self).destroy()
