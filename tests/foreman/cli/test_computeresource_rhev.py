"""
:Requirement: Computeresource RHV

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ComputeResources-RHEV

:Assignee: lhellebr

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
from robottelo.cli.factory import make_os
from robottelo.config import settings
from robottelo.decorators import skip_if_not_set
from robottelo.test import CLITestCase


class RHEVComputeResourceTestCase(CLITestCase):
    """RHEVComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('rhev')
    def setUpClass(cls):
        super().setUpClass()
        cls.current_rhev_url = settings.rhev.hostname
        cls.username = settings.rhev.username
        cls.password = settings.rhev.password
        cls.datacenter = settings.rhev.datacenter
        cls.image_arch = settings.rhev.image_arch
        cls.image_uuid = settings.rhev.image_uuid
        cls.os = make_os()

    @pytest.mark.tier1
    def test_positive_create_rhev_with_valid_name(self):
        """Create Compute Resource of type Rhev with valid name

        :id: 92a577db-144e-4761-a52e-e83887464986

        :expectedresults: Compute resource is created

        :CaseImportance: Critical

        :BZ: 1602835
        """
        ComputeResource.create(
            {
                'name': 'cr {}'.format(gen_string(str_type='alpha')),
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )

    @pytest.mark.tier1
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
                'name': name,
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertEquals(compute_resource['name'], name)

    @pytest.mark.tier1
    def test_positive_delete_by_name(self):
        """Delete the RHEV compute resource by name

        :id: ac84acbe-3e02-4f49-9695-b668df28b353

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1602835
        """
        comp_res = make_compute_resource(
            {
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'name': comp_res['name']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    @pytest.mark.tier1
    def test_positive_delete_by_id(self):
        """Delete the RHEV compute resource by id

        :id: 4bcd4fa3-df8b-4773-b142-e47458116552

        :expectedresults: Compute resource is deleted

        :CaseImportance: Critical

        :BZ: 1602835
        """
        comp_res = make_compute_resource(
            {
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.delete({'id': comp_res['id']})
        result = ComputeResource.exists(search=('name', comp_res['name']))
        self.assertFalse(result)

    @pytest.mark.tier2
    def test_negative_create_rhev_with_url(self):
        """RHEV compute resource negative create with invalid values

        :id: 1f318a4b-8dca-491b-b56d-cff773ed624e

        :expectedresults: Compute resource is not created

        :CaseImportance: High
        """
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.create(
                {
                    'provider': 'Ovirt',
                    'user': self.username,
                    'password': self.password,
                    'datacenter': self.datacenter,
                    'url': 'invalid url',
                }
            )

    @pytest.mark.tier2
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
                'name': name,
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertEquals(compute_resource['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_compute_resource(
                {
                    'name': name,
                    'provider': 'Ovirt',
                    'user': self.username,
                    'password': self.password,
                    'datacenter': self.datacenter,
                    'url': self.current_rhev_url,
                }
            )

    @pytest.mark.tier1
    @pytest.mark.upgrade
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
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.update({'name': comp_res['name'], 'new-name': new_name})
        self.assertEqual(new_name, ComputeResource.info({'id': comp_res['id']})['name'])

    @pytest.mark.tier2
    def test_positive_add_image_rhev_with_name(self):
        """Add images to the RHEV compute resource

        :id: 2da84165-a56f-4282-9343-94828fa69c13

        :setup: Images/templates should be present in RHEV-M itself,
            so that satellite can use them.

        :steps:

            1. Create a compute resource of type rhev.
            2. Create a image for the compute resource with valid parameter,
               compute-resource image create

        :expectedresults: The image is added to the CR successfully
        """
        if self.image_uuid is None:
            self.skipTest('Missing configuration for rhev.image_uuid')

        comp_res = make_compute_resource(
            {
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        ComputeResource.image_create(
            {
                'compute-resource': comp_res['name'],
                'name': 'img {}'.format(gen_string(str_type='alpha')),
                'uuid': self.image_uuid,
                'operatingsystem': self.os['title'],
                'architecture': self.image_arch,
                'username': "root",
            }
        )
        result = ComputeResource.image_list({'compute-resource': comp_res['name']})
        self.assertEqual(result[0]['uuid'], self.image_uuid)

    @pytest.mark.skip_if_open("BZ:1829239")
    @pytest.mark.tier2
    def test_negative_add_image_rhev_with_invalid_uuid(self):
        """Attempt to add invalid image to the RHEV compute resource

        :id: e8a653f9-9749-4c76-95ed-2411a7c0a117

        :setup: Images/templates should be present in RHEV-M itself,
            so that satellite can use them.

        :steps:

            1. Create a compute resource of type rhev.
            2. Create a image for the compute resource with invalid value for
               uuid parameter, compute-resource image create.

        :expectedresults: The image should not be added to the CR

        :BZ: 1829239
        """
        comp_res = make_compute_resource(
            {
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )
        self.assertTrue(comp_res['name'])
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.image_create(
                {
                    'compute-resource': comp_res['name'],
                    'name': 'img {}'.format(gen_string(str_type='alpha')),
                    'uuid': 'invalidimguuid {}'.format(gen_string(str_type='alpha')),
                    'operatingsystem': self.os['title'],
                    'architecture': self.image_arch,
                    'username': "root",
                }
            )

    @pytest.mark.tier2
    def test_negative_add_image_rhev_with_invalid_name(self):
        """Attempt to add invalid image name to the RHEV compute resource

        :id: 873a7d79-1e89-4e4f-81ca-b6db1e0246da

        :setup: Images/templates should be present in RHEV-M itself,
            so that satellite can use them.

        :steps:

            1. Create a compute resource of type rhev.
            2. Create a image for the compute resource with invalid value for
               name parameter, compute-resource image create.

        :expectedresults: The image should not be added to the CR

        """
        if self.image_uuid is None:
            self.skipTest('Missing configuration for rhev.image_uuid')

        comp_res = make_compute_resource(
            {
                'provider': 'Ovirt',
                'user': self.username,
                'password': self.password,
                'datacenter': self.datacenter,
                'url': self.current_rhev_url,
            }
        )

        self.assertTrue(comp_res['name'])
        with self.assertRaises(CLIReturnCodeError):
            ComputeResource.image_create(
                {
                    'compute-resource': comp_res['name'],
                    # too long string (>255 chars)
                    'name': 'img {}'.format(gen_string(str_type='alphanumeric', length=256)),
                    'uuid': self.image_uuid,
                    'operatingsystem': self.os['title'],
                    'architecture': self.image_arch,
                    'username': "root",
                }
            )

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
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

        :CaseAutomation: NotAutomated

        :CaseLevel: Integration
        """
