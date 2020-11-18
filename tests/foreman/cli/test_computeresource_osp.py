# -*- encoding: utf-8 -*-
"""
:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-OpenStack

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import CLIReturnCodeError
from robottelo.cli.factory import make_compute_resource
from robottelo.config import settings
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class OSPComputeResourceTestCase(CLITestCase):
    """OSPComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('osp')
    def setUpClass(cls):
        super(OSPComputeResourceTestCase, cls).setUpClass()
        cls.current_osp_url = settings.osp.hostname
        cls.username = settings.osp.username
        cls.password = settings.osp.password
        cls.tenant = settings.osp.tenant
        cls.domain_id = settings.osp.project_domain_id

    @tier1
    def test_positive_create_osp_with_valid_name(self):
        """Create Compute Resource of type Openstack with valid name

        :id: 064c939f-b2da-4b49-b784-24559f296cd9

        :expectedresults: Compute resource is created

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        with self.assertNotRaises(CLIReturnCodeError):
            compute_resource = ComputeResource.create(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': self.current_osp_url,
                    'project-domain-id': self.domain_id,
                }
            )
            self.assertEqual(compute_resource['name'], name)

    @tier3
    def test_positive_osp_info(self):
        """List the info of Openstack compute resource

        :id: 8ed9f9e6-053a-402d-8f3d-3ba46300098d

        :expectedresults: OSP Compute resource Info is displayed

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        with self.assertNotRaises(CLIReturnCodeError):
            compute_resource = make_compute_resource(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': self.current_osp_url,
                    'project-domain-id': self.domain_id,
                }
            )
            self.assertEqual(compute_resource['name'], name)
            self.assertIsNotNone(compute_resource['id'])

    @tier3
    def test_positive_delete_by_name(self):
        """Delete the Openstack compute resource by name

        :id: 8c581100-4606-4d21-a286-930fb3a7ecd8

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1579714
        """
        with self.assertNotRaises(CLIReturnCodeError):
            comp_res = make_compute_resource(
                {
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': self.current_osp_url,
                    'project-domain-id': self.domain_id,
                }
            )
            self.assertTrue(comp_res['name'])
            ComputeResource.delete({'name': comp_res['name']})
            result = ComputeResource.exists(search=('name', comp_res['name']))
            self.assertFalse(result)

    @tier3
    @upgrade
    def test_positive_delete_by_id(self):
        """Delete the Openstack compute resource by id

        :id: f464429f-a4ac-4504-b009-5f56f9d29317

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1579714
        """
        with self.assertNotRaises(CLIReturnCodeError):
            comp_res = make_compute_resource(
                {
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': self.current_osp_url,
                    'project-domain-id': self.domain_id,
                }
            )
            self.assertTrue(comp_res['name'])
            ComputeResource.delete({'id': comp_res['id']})
            result = ComputeResource.exists(search=('name', comp_res['name']))
            self.assertFalse(result)

    @tier3
    def test_negative_create_osp_with_url(self):
        """Attempt to create Openstack compute resource with invalid URL

        :id: a6be8233-2641-4c87-8563-f48d6efbb6ac

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': 'invalid url',
                    'project-domain-id': self.domain_id,
                }
            )

    @tier3
    def test_negative_create_with_same_name(self):
        """Attempt to create Openstack compute resource with the same name as
        an existing one

        :id: b08132fe-6081-48e9-b7fd-9da7966aef5d

        :steps:

            1. Create a osp compute resource.
            2. Create another osp compute resource with same name.

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        compute_resource = make_compute_resource(
            {
                'name': name,
                'provider': 'Openstack',
                'user': self.username,
                'password': self.password,
                'tenant': self.tenant,
                'url': self.current_osp_url,
                'project-domain-id': self.domain_id,
            }
        )
        self.assertEqual(compute_resource['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_compute_resource(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': self.username,
                    'password': self.password,
                    'tenant': self.tenant,
                    'url': self.current_osp_url,
                    'project-domain-id': self.domain_id,
                }
            )

    @tier3
    def test_positive_update_name(self):
        """Update Openstack compute resource name

        :id: 16eb2def-34d5-49c5-be22-88139fef7f97

        :steps:

            1. Create a osp compute resource
            2. Update the name of the created compute resource

        :expectedresults: Compute Resource name is successfully updated

        :CaseImportance: Critical

        :BZ: 1579714
        """
        new_name = gen_string('alpha')
        comp_res = make_compute_resource(
            {
                'provider': 'Openstack',
                'user': self.username,
                'password': self.password,
                'tenant': self.tenant,
                'url': self.current_osp_url,
                'project-domain-id': self.domain_id,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.update({'name': comp_res['name'], 'new-name': new_name})
        self.assertEqual(new_name, ComputeResource.info({'id': comp_res['id']})['name'])

    @tier3
    @pytest.mark.stubbed
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

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
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

        :CaseAutomation: NotAutomated
        """
