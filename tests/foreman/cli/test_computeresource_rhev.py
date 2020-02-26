# -*- encoding: utf-8 -*-
"""
:Requirement: Computeresource RHV

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ComputeResources-RHEV

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import CLIReturnCodeError
from robottelo.cli.factory import make_compute_resource
from robottelo.config import settings
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class RHEVComputeResourceTestCase(CLITestCase):
    """RHEVComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('rhev')
    def setUpClass(cls):
        super(RHEVComputeResourceTestCase, cls).setUpClass()
        cls.current_rhev_url = settings.rhev.hostname
        cls.username = settings.rhev.username
        cls.passord = settings.rhev.password
        cls.datacenter = settings.rhev.datacenter

    @tier1
    def test_positive_create_rhev_with_valid_name(self):
        """Create Compute Resource of type Rhev with valid name

        :id: 92a577db-144e-4761-a52e-e83887464986

        :expectedresults: Compute resource is created

        :CaseImportance: Critical

        :BZ: 1602835
        """
        ComputeResource.create(
            {
                u'name': 'cr {0}'.format(gen_string(str_type='alpha')),
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )

    @tier1
    def test_positive_rhev_info(self):
        """List the info of RHEV compute resource

        :id: 1b18f6e8-c431-41ab-ae49-a2bbb74712f2

        :expectedresults: RHEV Compute resource Info is displayed

        :CaseImportance: Critical

        :BZ: 1602835
        """
        name = gen_string('utf8')
        compute_resource = make_compute_resource(
            {
                u'name': name,
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )
        self.assertEquals(compute_resource['name'], name)

    @tier1
    def test_positive_delete_by_name(self):
        """Delete the RHEV compute resource by name

        :id: ac84acbe-3e02-4f49-9695-b668df28b353

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1602835
        """
        comp_res = make_compute_resource(
            {
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'name': comp_res['name']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    @tier1
    def test_positive_delete_by_id(self):
        """Delete the RHEV compute resource by id

        :id: 4bcd4fa3-df8b-4773-b142-e47458116552

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1602835
        """
        comp_res = make_compute_resource(
            {
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'id': comp_res['id']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    @tier2
    def test_negative_create_rhev_with_url(self):
        """RHEV compute resource negative create with invalid values

        :id: 1f318a4b-8dca-491b-b56d-cff773ed624e

        :expectedresults: Compute resource is not created

        :CaseImportance: High
        """
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create(
                {
                    u'provider': 'Ovirt',
                    u'user': self.username,
                    u'password': self.passord,
                    u'datacenter': self.datacenter,
                    u'url': 'invalid url',
                }
            )

    @tier2
    def test_negative_create_with_same_name(self):
        """RHEV compute resource negative create with the same name

        :id: f00813ef-df31-462c-aa87-479b8272aea3

        :steps:

            1. Create a RHEV compute resource.
            2. Create another RHEV compute resource with same name.

        :expectedresults: Compute resource is not created

        :CaseImportance: High
        """
        name = gen_string('alpha')
        compute_resource = make_compute_resource(
            {
                u'name': name,
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )
        self.assertEquals(compute_resource['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_compute_resource(
                {
                    u'name': name,
                    u'provider': 'Ovirt',
                    u'user': self.username,
                    u'password': self.passord,
                    u'datacenter': self.datacenter,
                    u'url': self.current_rhev_url,
                }
            )

    @tier1
    @upgrade
    def test_positive_update_name(self):
        """RHEV compute resource positive update

        :id: 5ca29b81-d1f0-409f-843d-aa5daf957d7f

        :steps:

            1. Create a RHEV compute resource
            2. Update the name of the created compute resource

        :expectedresults: Compute Resource is successfully updated

        :CaseImportance: Critical

        :BZ: 1602835
        """
        new_name = gen_string('alpha')
        comp_res = make_compute_resource(
            {
                u'provider': 'Ovirt',
                u'user': self.username,
                u'password': self.passord,
                u'datacenter': self.datacenter,
                u'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.update({'name': comp_res['name'], 'new-name': new_name})
        self.assertEqual(new_name, ComputeResource.info({'id': comp_res['id']})['name'])

    @tier2
    @stubbed()
    def test_positive_add_image_rhev_with_name(self):
        """Add images to the RHEV compute resource

        :id: 2da84165-a56f-4282-9343-94828fa69c13

        :setup: Images/templates should be present in RHEV-M itself,
            so that satellite can use them.

        :steps:

            1. Create a compute resource of type rhev.
            2. Create a image for the compute resource with valid parameter,
               compute-resource image create

        :CaseAutomation: notautomated

        :expectedresults: The image is added to the CR successfully
         """

    @tier2
    @stubbed()
    def test_negative_add_image_rhev_with_invalid_name(self):
        """Attempt to add invalid image to the RHEV compute resource

        :id: e8a653f9-9749-4c76-95ed-2411a7c0a117

        :setup: Images/templates should be present in RHEV-M itself,
            so that satellite can use them.

        :steps:

            1. Create a compute resource of type rhev.
            2. Create a image for the compute resource with invalid value for
               name parameter, compute-resource image create.

        :CaseAutomation: notautomated

        :expectedresults: The image should not be added to the CR
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_rhev_without_host_group(self):
        """Provision a host on RHEV compute resource without
        the help of hostgroup.

        :id: 861940cb-1550-4f00-9df2-5a45683635b1

        :setup: Provisioning setup like domain, subnet etc.

        :steps:

            1. Create a RHEV compute resource.
            2. Create a host on RHEV compute resource.
            3. Use compute-attributes parameter to specify key-value parameters
               regarding the virtual machine.
            4. Provision the host.

        :expectedresults: The host should be provisioned successfully

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """
