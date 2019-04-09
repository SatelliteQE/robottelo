# -*- encoding: utf-8 -*-
"""
:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi import RHEVMSystem, VMWareSystem

from robottelo.api.utils import configure_provisioning
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import (
    make_compute_resource,
    make_host
)
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, VMWARE_CONSTANTS
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    bz_bug_is_open,
    tier3,
)
from robottelo.helpers import ProvisioningCheckError, host_provisioning_check
from robottelo.test import CLITestCase


class ComputeResourceHostTestCase(CLITestCase):
    """RHEVComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('rhev')
    def setUpClass(cls):
        super(ComputeResourceHostTestCase, cls).setUpClass()
        bridge = settings.vlan_networking.bridge
        # RHV Settings
        cls.rhev_url = settings.rhev.hostname
        cls.rhev_password = settings.rhev.password
        cls.rhev_username = settings.rhev.username
        cls.rhev_datacenter = settings.rhev.datacenter
        cls.rhev_img_name = settings.rhev.image_name
        cls.rhev_img_arch = settings.rhev.image_arch
        cls.rhev_img_os = settings.rhev.image_os
        cls.rhev_img_user = settings.rhev.image_username
        cls.rhev_img_pass = settings.rhev.image_password
        cls.rhev_vm_name = settings.rhev.vm_name
        cls.rhev_storage_domain = settings.rhev.storage_domain
        cls.rhv_api = RHEVMSystem(hostname=cls.rhev_url.split('/')[2],
                                  username=cls.rhev_username,
                                  password=cls.rhev_password,
                                  version='4.0',
                                  verify=False
                                  )
        cls.cluster_id = cls.rhv_api.get_cluster(cls.rhev_datacenter).id
        cls.storage_id = cls.rhv_api.get_storage_domain(
            cls.rhev_storage_domain).id
        cls.network_id = (
            cls.rhv_api.api.system_service().networks_service(
            ).list(search='name={0}'.format(bridge))[0].id
        )
        if bz_bug_is_open(1685949):
            dc = cls.rhv_api._data_centers_service.list(
                search='name={0}'.format(cls.rhev_datacenter))[0]
            dc = cls.rhv_api._data_centers_service.data_center_service(dc.id)
            cls.quota = dc.quotas_service().list()[0].id
        else:
            cls.quota = 'Default'

        # Vmware Settings
        cls.vmware_server = settings.vmware.vcenter
        cls.vmware_password = settings.vmware.password
        cls.vmware_username = settings.vmware.username
        cls.vmware_datacenter = settings.vmware.datacenter
        cls.vmware_img_name = settings.vmware.image_name
        cls.vmware_img_arch = settings.vmware.image_arch
        cls.vmware_img_os = settings.vmware.image_os
        cls.vmware_img_user = settings.vmware.image_username
        cls.vmware_img_pass = settings.vmware.image_password
        cls.vmware_vm_name = settings.vmware.vm_name
        cls.current_interface = (
                VMWARE_CONSTANTS.get('network_interfaces') % bridge
        )
        cls.vmware_api = VMWareSystem(hostname=cls.vmware_server,
                                      username=cls.vmware_username,
                                      password=cls.vmware_password
                                      )
        cls.vmware_net_id = cls.vmware_api.get_network(
            cls.current_interface)._moId

        # Provisioning setup
        cls.org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org],
        ).create()
        cls.loc_name = cls.loc.name
        cls.config_env = configure_provisioning(
            compute=True,
            org=cls.org,
            loc=cls.loc,
            os=cls.rhev_img_os
        )
        cls.os_name = cls.config_env['os']

    def tearDown(self):
        """Delete the host to free the resources"""
        super(ComputeResourceHostTestCase, self).tearDown()
        hosts = Host.list({'organization': self.org_name})
        for host in hosts:
            Host.delete({'id': host['id']})

    @tier3
    @run_only_on('sat')
    def test_positive_provision_rhev_with_host_group(self):
        """Provision a host on RHEV compute resource with
        the help of hostgroup.

        :Requirement: Computeresource RHV

        :id: ba78868f-5cff-462f-a55d-f6aa4d11db52

        :setup: Hostgroup and provisioning setup like domain, subnet etc.

        :steps:

            1. Create a RHEV compute resource.
            2. Create a host on RHEV compute resource using the Hostgroup
            3. Use compute-attributes parameter to specify key-value parameters
               regarding the virtual machine.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :CaseAutomation: automated
        """
        name = gen_string('alpha')
        rhv_cr = ComputeResource.create({
            u'name': name,
            u'provider': 'Ovirt',
            u'user': self.rhev_username,
            u'password': self.rhev_password,
            u'datacenter': self.rhev_datacenter,
            u'url': self.rhev_url,
            u'ovirt-quota': self.quota,
            u'organizations': self.org_name,
            u'locations': self.loc_name
        })
        self.assertEquals(rhv_cr['name'], name)
        host_name = gen_string('alpha').lower()
        host = make_host({
            'name': '{0}'.format(host_name),
            'root-password': gen_string('alpha'),
            'organization': self.org_name,
            'location': self.loc_name,
            'pxe-loader': 'PXELinux BIOS',
            'hostgroup': self.config_env['host_group'],
            'compute-resource-id': rhv_cr.get('id'),
            'compute-attributes': "cluster={0},"
                                  "cores=1,"
                                  "memory=1073741824,"
                                  "start=1".format(self.cluster_id),
            'ip': None,
            'mac': None,
            'interface': "compute_name=nic1, "
                         "compute_network={0}".format(self.network_id),
            'volume': "size_gb=10,"
                      "storage_domain={0},"
                      "bootable=True".format(self.storage_id),
            'provision-method': 'build'
        })
        hostname = '{0}.{1}'.format(
                host_name, self.config_env['domain'])
        self.assertEquals(hostname, host['name'])
        host_info = Host.info({'name': hostname})
        host_ip = host_info.get('network').get('ipv4-address')
        # Check on RHV, if VM exists
        self.assertTrue(self.rhv_api.does_vm_exist(hostname))
        # Get the information of created VM
        rhv_vm = self.rhv_api.get_vm(hostname)
        # Assert of Satellite mac address for VM and Mac of VM created is same
        self.assertEqual(host_info.get('network').get('mac'),
                         rhv_vm.get_nics()[0].mac.address
                         )
        # Start to run a ping check if network was established on VM
        with self.assertNotRaises(ProvisioningCheckError):
            host_provisioning_check(ip_addr=host_ip)

    @run_only_on('sat')
    @tier3
    def test_positive_provision_vmware_with_host_group(self):
        """ Provision a host on vmware compute resource with
        the help of hostgroup.

        :Requirement: Computeresource Vmware

        :id: ae4d5949-f0e6-44ca-93b6-c5241a02b64b

        :setup:

            1. Vaild vmware hostname ,credentials.
            2. Configure provisioning setup.
            3. Configure host group setup.

        :steps:

            1. Go to "Hosts --> New host".
            2. Assign the host group to the host.
            3. Select the Deploy on as vmware Compute Resource.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :CaseAutomation: Automated

        :CaseLevel: System
        """
        cr_name = gen_string('alpha')
        vmware_cr = make_compute_resource({
            'name': cr_name,
            'organizations': self.org_name,
            'locations': self.loc_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': self.vmware_server,
            'user': self.vmware_username,
            'password': self.vmware_password,
            'datacenter': self.vmware_datacenter
        })
        self.assertEquals(vmware_cr['name'], cr_name)
        host_name = gen_string('alpha').lower()
        host = make_host({
            'name': '{0}'.format(host_name),
            'root-password': gen_string('alpha'),
            'organization': self.org_name,
            'location': self.loc_name,
            'hostgroup': self.config_env['host_group'],
            'pxe-loader': 'PXELinux BIOS',
            'compute-resource-id': vmware_cr.get('id'),
            'compute-attributes': "cpus=2,"
                                  "corespersocket=2,"
                                  "memory_mb=4028,"
                                  "cluster={0},"
                                  "path=/Datacenters/{1}/vm/QE,"
                                  "guest_id=rhel7_64Guest,"
                                  "scsi_controller_type=VirtualLsiLogic,"
                                  "hardware_version=Default,"
                                  "start=1".format(VMWARE_CONSTANTS['cluster'],
                                                   self.vmware_datacenter
                                                   ),
            'ip': None,
            'mac': None,
            'interface': "compute_network={0},"
                         "compute_type=VirtualVmxnet3".format(
                self.vmware_net_id),
            'volume': "name=Hard disk,"
                      "size_gb=10,"
                      "thin=true,"
                      "eager_zero=false,"
                      "datastore={0}".format(
                VMWARE_CONSTANTS['datastore'].split()[0]
            ),
            'provision-method': 'build'
        })
        hostname = '{0}.{1}'.format(
            host_name, self.config_env['domain'])
        self.assertEquals(hostname, host['name'])
        # Check on Vmware, if VM exists
        self.assertTrue(self.vmware_api.does_vm_exist(hostname))
        host_info = Host.info({'name': hostname})
        host_ip = host_info.get('network').get('ipv4-address')
        # Start to run a ping check if network was established on VM
        with self.assertNotRaises(ProvisioningCheckError):
            host_provisioning_check(ip_addr=host_ip)
