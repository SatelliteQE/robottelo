# -*- encoding: utf-8 -*-
"""
:Requirement: Computeresource Vmware

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-VMWare

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, VMWARE_CONSTANTS
from robottelo.cli.factory import (
    make_compute_resource,
    make_location,
    make_org,
)
from robottelo.cli.org import Org
from robottelo.decorators import (
    skip_if_not_set,
    tier1,
    upgrade
)
from robottelo.test import CLITestCase


class VMWareComputeResourceTestCase(CLITestCase):
    """VMware ComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('vmware')
    def setUpClass(cls):
        super(VMWareComputeResourceTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.loc = make_location()
        Org.add_location({'id': cls.org['id'], 'location-id': cls.loc['id']})
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
            VMWARE_CONSTANTS.get(
                'network_interfaces') % settings.vlan_networking.bridge
        )

    @tier1
    def test_positive_create_with_server(self):
        """Create VMware compute resource with server field

        :id: a06b02c4-fe6a-44ef-bf61-5a28c3905527

        :customerscenario: true

        :expectedresults: Compute resource is created, server field saved
            correctly

        :BZ: 1387917

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        cr_name = gen_string('alpha')
        vmware_cr = make_compute_resource({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': self.vmware_server,
            'user': self.vmware_username,
            'password': self.vmware_password,
            'datacenter': self.vmware_datacenter
        })
        self.assertEquals(vmware_cr['name'], cr_name)
        self.assertEquals(vmware_cr['server'], self.vmware_server)

    @tier1
    def test_positive_create_with_org(self):
        """Create VMware Compute Resource with organizations

        :id: 807a1f70-4cc3-4925-b145-0c3b26c57559

        :customerscenario: true

        :expectedresults: VMware Compute resource is created

        :BZ: 1387917

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        cr_name = gen_string('alpha')
        vmware_cr = make_compute_resource({
            'name': cr_name,
            'organization-ids': self.org['id'],
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': self.vmware_server,
            'user': self.vmware_username,
            'password': self.vmware_password,
            'datacenter': self.vmware_datacenter
        })
        self.assertEquals(vmware_cr['name'], cr_name)

    @tier1
    def test_positive_create_with_loc(self):
        """Create VMware Compute Resource with locations

        :id: 214a0f54-6fc2-4e7b-91ab-a45760ffb2f2

        :customerscenario: true

        :expectedresults: VMware Compute resource is created

        :BZ: 1387917

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        cr_name = gen_string('alpha')
        vmware_cr = make_compute_resource({
            'name': cr_name,
            'location-ids': self.loc['id'],
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': self.vmware_server,
            'user': self.vmware_username,
            'password': self.vmware_password,
            'datacenter': self.vmware_datacenter
        })
        self.assertEquals(vmware_cr['name'], cr_name)

    @tier1
    @upgrade
    def test_positive_create_with_org_and_loc(self):
        """Create VMware Compute Resource with organizations and locations

        :id: 96faae3f-bc64-4147-a9fc-09c858e0a68f

        :customerscenario: true

        :expectedresults: VMware Compute resource is created

        :BZ: 1387917

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        cr_name = gen_string('alpha')
        vmware_cr = make_compute_resource({
            'name': cr_name,
            'organization-ids': self.org['id'],
            'location-ids': self.loc['id'],
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': self.vmware_server,
            'user': self.vmware_username,
            'password': self.vmware_password,
            'datacenter': self.vmware_datacenter
        })
        self.assertEquals(vmware_cr['name'], cr_name)
