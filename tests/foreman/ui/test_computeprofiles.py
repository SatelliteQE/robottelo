"""Test class for Compute Profile UI

:Requirement: Computeprofile

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_location, module_org):
    """Perform end to end testing for compute profile component

    :id: 5445fc7e-7b3f-472f-8a94-93f89aca6c22

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    compute_resource = entities.LibvirtComputeResource(
        location=[module_location], organization=[module_org], url='qemu+ssh://root@test/system'
    ).create()
    with session:
        session.computeprofile.create({'name': name})

        assert entities.ComputeProfile().search(query={'search': f'name={name}'}), (
            'Compute profile {} expected to exist, but is not included in the search '
            'results'.format(name)
        )
        compute_resource_list = session.computeprofile.list_resources(name)
        assert f'{compute_resource.name} (Libvirt)' in [
            resource['Compute Resource'] for resource in compute_resource_list
        ]
        session.computeprofile.rename(name, {'name': new_name})
        assert entities.ComputeProfile().search(query={'search': f'name={new_name}'}), (
            'Compute profile {} expected to exist, but is not included in the search '
            'results'.format(new_name)
        )
        session.computeprofile.delete(new_name)
        assert not entities.ComputeProfile().search(query={'search': f'name={new_name}'}), (
            'Compute profile {} expected to be deleted, but is included in the search '
            'results'.format(new_name)
        )
