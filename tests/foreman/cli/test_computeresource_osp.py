"""
:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-OpenStack

:Assignee: lvrtelov

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

OSP_SETTINGS = dict(
    username=settings.osp.username,
    password=settings.osp.password,
    tenant=settings.osp.tenant,
    hostname=settings.osp.hostname,
    project_domain_id=settings.osp.project_domain_id,
)


class TestOSPComputeResourceTestCase:
    """OSPComputeResource CLI tests."""

    def cr_cleanup(self, cr_id):
        """Finalizer for removing CR from Satellite.
        This should remove ssh key pairs from OSP in case of test fail.
        """
        try:
            ComputeResource.delete({'id': cr_id})
        except CLIReturnCodeError:
            pass

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize('id_type', ['id', 'name'])
    def test_crud_and_duplicate_name(self, request, id_type):
        """Create, list, update and delete Openstack compute resource

        :id: caf60bad-999d-483e-807f-95f52f35085d

        :expectedresults: OSP Compute resource can be created updated and deleted

        :CaseImportance: Critical

        :parametrized: yes

        :BZ: 1579714
        """
        # create
        name = gen_string('alpha')
        compute_resource = make_compute_resource(
            {
                'name': name,
                'provider': 'Openstack',
                'user': OSP_SETTINGS['username'],
                'password': OSP_SETTINGS['password'],
                'tenant': OSP_SETTINGS['tenant'],
                'url': OSP_SETTINGS['hostname'],
                'project-domain-id': OSP_SETTINGS['project_domain_id'],
            }
        )
        request.addfinalizer(lambda: self.cr_cleanup(compute_resource['id']))
        assert compute_resource['name'] == name
        assert ComputeResource.exists(search=(id_type, compute_resource[id_type]))

        # negative create with same name
        with pytest.raises(CLIFactoryError):
            make_compute_resource(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': OSP_SETTINGS['username'],
                    'password': OSP_SETTINGS['password'],
                    'tenant': OSP_SETTINGS['tenant'],
                    'url': OSP_SETTINGS['hostname'],
                    'project-domain-id': OSP_SETTINGS['project_domain_id'],
                }
            )
        # update
        new_name = gen_string('alpha')
        ComputeResource.update({id_type: compute_resource[id_type], 'new-name': new_name})
        if id_type == 'name':
            compute_resource = ComputeResource.info({'name': new_name})
        else:
            compute_resource = ComputeResource.info({'id': compute_resource['id']})
        assert new_name == compute_resource['name']
        ComputeResource.delete({id_type: compute_resource[id_type]})
        assert not ComputeResource.exists(search=(id_type, compute_resource[id_type]))

    @pytest.mark.tier3
    def test_negative_create_osp_with_url(self):
        """Attempt to create Openstack compute resource with invalid URL

        :id: a6be8233-2641-4c87-8563-f48d6efbb6ac

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        with pytest.raises(CLIReturnCodeError):
            ComputeResource.create(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': OSP_SETTINGS['username'],
                    'password': OSP_SETTINGS['password'],
                    'tenant': OSP_SETTINGS['tenant'],
                    'url': 'invalid url',
                    'project-domain-id': OSP_SETTINGS['project_domain_id'],
                }
            )

    @pytest.mark.tier3
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
    @pytest.mark.tier3
    @pytest.mark.upgrade
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
