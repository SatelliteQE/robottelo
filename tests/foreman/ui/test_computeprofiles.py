"""Test class for Compute Profile UI

:Requirement: Computeprofile

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.decorators import tier2, upgrade


@tier2
@upgrade
def test_positive_end_to_end(session, module_loc, module_org):
    """Perform end to end testing for compute profile component

    :id: 5445fc7e-7b3f-472f-8a94-93f89aca6c22

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    compute_resource = entities.LibvirtComputeResource(
        location=[module_loc],
        organization=[module_org],
        url='qemu+ssh://root@test/system'
    ).create()
    with session:
        session.computeprofile.create({'name': name})
        assert session.computeprofile.search(name)[0]['Name'] == name
        compute_resource_list = session.computeprofile.list_resources(name)
        assert (
            '{} (Libvirt)'.format(compute_resource.name) in
            [resource['Compute Resource'] for resource in compute_resource_list]
        )
        session.computeprofile.rename(name, {'name': new_name})
        assert session.computeprofile.search(new_name)[0]['Name'] == new_name
        session.computeprofile.delete(new_name)
        assert not session.computeprofile.search(new_name)
