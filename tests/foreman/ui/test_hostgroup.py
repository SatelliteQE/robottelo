"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseComponent: HostGroup

:CaseLevel: Integration

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT


@pytest.mark.tier2
def test_positive_end_to_end(session, module_org, module_location):
    """Perform end to end testing for host group component

    :id: 537d95f2-fe32-4e06-a2cb-21c80fe8e2e2

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = entities.Architecture().create()
    os = entities.OperatingSystem(architecture=[architecture]).create()
    os_name = f'{os.name} {os.major}'
    domain = entities.Domain(organization=[module_org], location=[module_location]).create()
    with session:
        # Create host group with some data
        session.hostgroup.create(
            {
                'host_group.name': name,
                'host_group.description': description,
                'host_group.lce': ENVIRONMENT,
                'host_group.content_view': DEFAULT_CV,
                'network.domain': domain.name,
                'operating_system.architecture': architecture.name,
                'operating_system.operating_system': os_name,
            }
        )
        hostgroup_values = session.hostgroup.read(name)
        assert hostgroup_values['host_group']['name'] == name
        assert hostgroup_values['host_group']['description'] == description
        assert hostgroup_values['host_group']['lce'] == ENVIRONMENT
        assert hostgroup_values['host_group']['content_view'] == DEFAULT_CV
        assert hostgroup_values['operating_system']['architecture'] == architecture.name
        assert hostgroup_values['operating_system']['operating_system'] == os_name
        # Update host group with new name
        session.hostgroup.update(name, {'host_group.name': new_name})
        assert session.hostgroup.search(new_name)[0]['Name'] == new_name
        # Delete host group
        session.hostgroup.delete(new_name)
        assert not entities.HostGroup().search(query={'search': f'name={new_name}'})


@pytest.mark.tier2
def test_negative_delete_with_discovery_rule(session, module_org, module_location):
    """Attempt to delete hostgroup which has dependent discovery rule

    :id: bd046e9a-f0d0-4110-8f94-fd04193cb3af

    :customerscenario: true

    :BZ: 1254102

    :expectedresults: Hostgroup was not deleted. Informative error message
        was shown

    :CaseImportance: High
    """
    hostgroup = entities.HostGroup(organization=[module_org], location=[module_location]).create()
    entities.DiscoveryRule(
        hostgroup=hostgroup, organization=[module_org], location=[module_location]
    ).create()
    with session:
        assert session.hostgroup.search(hostgroup.name)[0]['Name'] == hostgroup.name
        # Make an attempt to delete host group that associated with discovery rule
        with pytest.raises(AssertionError) as context:
            session.hostgroup.delete(hostgroup.name)
        assert "Cannot delete record because dependent discovery rules exist" in str(context.value)
        assert session.hostgroup.search(hostgroup.name)[0]['Name'] == hostgroup.name


@pytest.mark.stubbed
def test_positive_create_new_host():
    """Verify that content source field automatically populates when creating new host from host
    group.

    :id: 49704437-5ca1-46cb-b74e-de58396add37

    :Steps:

        1. Create hostgroup with the Content Source field populated.
        2. Create host from Hosts > Create Host, selecting the hostgroup in the Host Group field.

    :expectedresults: The host's Content source field is automatically populated from the selected
        hostgroup.

    :BZ: 1866746

    :customerscenario: true
    """
    pass


def test_positive_nested_host_groups(
    session, module_org, module_lce, module_published_cv, module_ak_cv_lce, target_sat
):
    """Verify create, update and delete operation for nested host-groups

    :id: 547f8e72-df65-48eb-aeb1-6b5fd3cbf4e5

    :Steps:

        1. Create the parent host-group.
        2. Create, Update and Delete the nested host-group.

    :CaseImportance: High

    :expectedresults: Crud operations with nest host-group should work as expected.

    :BZ: 1996077

    :customerscenario: true
    """
    parent_hg_name = gen_string('alpha')
    child_hg_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = target_sat.api.Architecture().create()
    os = target_sat.api.OperatingSystem(architecture=[architecture]).create()
    os_name = f'{os.name} {os.major}'
    with session:
        # Create parent host-group with default lce and content view
        session.hostgroup.create(
            {
                'host_group.name': parent_hg_name,
                'host_group.description': description,
                'host_group.lce': ENVIRONMENT,
                'host_group.content_view': DEFAULT_CV,
                'operating_system.architecture': architecture.name,
                'operating_system.operating_system': os_name,
            }
        )
        assert target_sat.api.HostGroup().search(query={'search': f'name={parent_hg_name}'})

        # Create nested host group
        session.hostgroup.create(
            {
                'host_group.parent_name': parent_hg_name,
                'host_group.name': child_hg_name,
            }
        )
        assert target_sat.api.HostGroup().search(query={'search': f'name={child_hg_name}'})
        child_hostgroup_values = session.hostgroup.read(f'{parent_hg_name}/{child_hg_name}')
        assert parent_hg_name in child_hostgroup_values['host_group']['parent_name']
        assert ENVIRONMENT in child_hostgroup_values['host_group']['lce']
        assert DEFAULT_CV in child_hostgroup_values['host_group']['content_view']

        # Update nested host group
        session.hostgroup.update(
            f'{parent_hg_name}/{child_hg_name}',
            {
                'host_group.lce': module_lce.name,
                'host_group.content_view': module_published_cv.name,
                'host_group.activation_keys': module_ak_cv_lce.name,
            },
        )
        child_hostgroup_values = session.hostgroup.read(f'{parent_hg_name}/{child_hg_name}')
        assert parent_hg_name in child_hostgroup_values['host_group']['parent_name']
        assert module_lce.name in child_hostgroup_values['host_group']['lce']
        assert module_published_cv.name in child_hostgroup_values['host_group']['content_view']

        # Delete nested host group
        session.hostgroup.delete(f'{parent_hg_name}/{child_hg_name}')
        assert not target_sat.api.HostGroup().search(query={'search': f'name={child_hg_name}'})
