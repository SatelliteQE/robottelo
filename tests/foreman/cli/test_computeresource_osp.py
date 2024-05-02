"""
:Requirement: Computeresource

:CaseAutomation: Automated

:CaseComponent: ComputeResources-OpenStack

:Team: Rocket

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.exceptions import CLIReturnCodeError

OSP_SETTINGS = Box(
    username=settings.osp.username,
    password=settings.osp.password,
    tenant=settings.osp.tenant,
    project_domain_id=settings.osp.project_domain_id,
)


class TestOSPComputeResourceTestCase:
    """OSPComputeResource CLI tests."""

    def cr_cleanup(self, cr_id, id_type, target_sat):
        """Finalizer for removing CR from Satellite.
        This should remove ssh key pairs from OSP in case of test fail.
        """
        try:
            target_sat.cli.ComputeResource.delete({id_type: cr_id})
            assert not target_sat.cli.ComputeResource.exists(search=(id_type, cr_id))
        except CLIReturnCodeError:
            pass

    @pytest.fixture
    def osp_version(request):
        versions = {'osp16': settings.osp.api_url.osp16, 'osp17': settings.osp.api_url.osp17}
        return versions[getattr(request, 'param', 'osp16')]

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize('osp_version', ['osp16', 'osp17'], indirect=True)
    @pytest.mark.parametrize(
        'id_type',
        ['id', 'name'],
    )
    def test_crud_and_duplicate_name(self, request, id_type, osp_version, target_sat):
        """Create, list, update and delete Openstack compute resource

        :id: caf60bad-999d-483e-807f-95f52f35085d

        :expectedresults: OSP Compute resource can be created updated and deleted

        :CaseImportance: Critical

        :parametrized: yes

        :BZ: 1579714
        """
        # create
        name = gen_string('alpha')
        compute_resource = target_sat.cli.ComputeResource.create(
            {
                'name': name,
                'provider': 'Openstack',
                'user': OSP_SETTINGS.username,
                'password': OSP_SETTINGS.password,
                'tenant': OSP_SETTINGS.tenant,
                'project-domain-id': OSP_SETTINGS.project_domain_id,
                'url': osp_version,
            }
        )
        request.addfinalizer(lambda: self.cr_cleanup(compute_resource['id'], id_type, target_sat))
        assert compute_resource['name'] == name
        assert target_sat.cli.ComputeResource.exists(search=(id_type, compute_resource[id_type]))

        # negative create with same name
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.ComputeResource.create(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': OSP_SETTINGS.username,
                    'password': OSP_SETTINGS.password,
                    'tenant': OSP_SETTINGS.tenant,
                    'project-domain-id': OSP_SETTINGS.project_domain_id,
                    'url': osp_version,
                }
            )
        # update
        new_name = gen_string('alpha')
        target_sat.cli.ComputeResource.update(
            {id_type: compute_resource[id_type], 'new-name': new_name}
        )
        if id_type == 'name':
            compute_resource = target_sat.cli.ComputeResource.info({'name': new_name})
        else:
            compute_resource = target_sat.cli.ComputeResource.info({'id': compute_resource['id']})
        assert new_name == compute_resource['name']

    @pytest.mark.tier3
    def test_negative_create_osp_with_url(self, target_sat):
        """Attempt to create Openstack compute resource with invalid URL

        :id: a6be8233-2641-4c87-8563-f48d6efbb6ac

        :expectedresults: Compute resource is not created

        :CaseImportance: Critical

        :BZ: 1579714
        """
        name = gen_string('alpha')
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.ComputeResource.create(
                {
                    'name': name,
                    'provider': 'Openstack',
                    'user': OSP_SETTINGS.username,
                    'password': OSP_SETTINGS.password,
                    'tenant': OSP_SETTINGS.tenant,
                    'project-domain-id': OSP_SETTINGS.project_domain_id,
                    'url': 'invalid_url',
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
