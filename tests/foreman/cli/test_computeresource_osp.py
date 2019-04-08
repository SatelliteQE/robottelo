# -*- encoding: utf-8 -*-
"""
:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import (
    CLIFactoryError,
    CLIReturnCodeError,
    make_compute_resource
)
from robottelo.config import settings
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier3,
    upgrade
)
from robottelo.test import CLITestCase


@skip_if_not_set('osp')
class OSPComputeResourceTestCase(CLITestCase):
    """OSPComputeResource CLI tests."""

    @classmethod
    def setUpClass(cls):
        super(OSPComputeResourceTestCase, cls).setUpClass()
        cls.current_osp_url = settings.osp.hostname
        cls.username = settings.osp.username
        cls.password = settings.osp.password
        cls.tenant = settings.osp.tenant

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_positive_create_osp_with_valid_name(self):
        """Create Compute Resource of type Openstack with valid name

        :id: 064c939f-b2da-4b49-b784-24559f296cd9

        :expectedresults: Compute resource is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with self.assertNotRaises(CLIReturnCodeError):
            compute_resource = ComputeResource.create({
                u'name': name,
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': self.current_osp_url
            })
            self.assertEquals(compute_resource['name'], name)

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_positive_osp_info(self):
        """List the info of Openstack compute resource

        :id: 8ed9f9e6-053a-402d-8f3d-3ba46300098d

        :expectedresults: OSP Compute resource Info is displayed

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with self.assertNotRaises(CLIReturnCodeError):
            compute_resource = make_compute_resource({
                u'name': name,
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': self.current_osp_url
            })
            self.assertEquals(compute_resource['name'], name)
            self.assertIsNotNone(compute_resource['id'])

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_positive_delete_by_name(self):
        """Delete the Openstack compute resource by name

        :id: 8c581100-4606-4d21-a286-930fb3a7ecd8

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical
        """
        with self.assertNotRaises(CLIReturnCodeError):
            comp_res = make_compute_resource({
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': self.current_osp_url
            })
            self.assertTrue(comp_res['name'])
            ComputeResource.delete({'name': comp_res['name']})
            result = ComputeResource.exists(search=('name', comp_res['name']))
            self.assertFalse(result)

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    @upgrade
    def test_positive_delete_by_id(self):
        """Delete the Openstack compute resource by id

        :id: f464429f-a4ac-4504-b009-5f56f9d29317

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical
        """
        with self.assertNotRaises(CLIReturnCodeError):
            comp_res = make_compute_resource({
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': self.current_osp_url
            })
            self.assertTrue(comp_res['name'])
            ComputeResource.delete({'id': comp_res['id']})
            result = ComputeResource.exists(search=('name', comp_res['name']))
            self.assertFalse(result)

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_negative_create_osp_with_url(self):
        """Attempt to create Openstack compute resource with invalid URL

        :id: a6be8233-2641-4c87-8563-f48d6efbb6ac

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create({
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': 'invalid url'
            })

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_negative_create_with_same_name(self):
        """Attempt to create Openstack compute resource with the same name as
        an existing one

        :id: b08132fe-6081-48e9-b7fd-9da7966aef5d

        :steps:

            1. Create a osp compute resource.
            2. Create another osp compute resource with same name.

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        compute_resource = make_compute_resource({
            u'name': name,
            u'provider': 'Openstack',
            u'user': self.username,
            u'password': self.password,
            u'tenant': self.tenant,
            u'url': self.current_osp_url
        })
        self.assertEquals(compute_resource['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_compute_resource({
                u'name': name,
                u'provider': 'Openstack',
                u'user': self.username,
                u'password': self.password,
                u'tenant': self.tenant,
                u'url': self.current_osp_url
            })

    @tier1
    @skip_if_bug_open('bugzilla', 1579714)
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update Openstack compute resource name

        :id: 16eb2def-34d5-49c5-be22-88139fef7f97

        :steps:

            1. Create a osp compute resource
            2. Update the name of the created compute resource

        :expectedresults: Compute Resource name is successfully updated

        :CaseImportance: Critical
        """
        new_name = gen_string('alpha')
        comp_res = make_compute_resource({
            u'provider': 'Openstack',
            u'user': self.username,
            u'password': self.password,
            u'tenant': self.tenant,
            u'url': self.current_osp_url
        })
        self.assertTrue(comp_res['name'])
        ComputeResource.update({
            'name': comp_res['name'],
            'new-name': new_name
        })
        self.assertEqual(
            new_name,
            ComputeResource.info({'id': comp_res['id']})['name']
        )

    @tier3
    @run_only_on('sat')
    @stubbed()
    def test_positive_provision_osp_with_host_group(self):
        """Provision a host on Openstack compute resource with
        the help of hostgroup.

        :id: d85df090-875f-4f2b-b0f2-708efd5f50f3

        :setup: Hostgroup and provisioning setup like domain, subnet etc.

        :steps:

            1. Create a osp compute resource.
            2. Create a hostgroup, with appropriate values
            3. Use compute-attributes parameter to specify key-value parameters
               regarding the virtual machine.
            4. Provision the host.

        :expectedresults: The host should be provisioned with host group

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_osp_without_host_group(self):
        """Provision a host on Openstack compute resource without
        the help of hostgroup.

        :id: 644000fc-a131-4df1-89ad-897f0c741f06

        :setup: Provisioning setup like domain, subnet etc.

        :steps:

            1. Create a osp compute resource.
            2. Use compute-attributes parameter to specify key-value parameters
               regarding the virtual machine.
            3. Provision the host.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: notautomated
        """
