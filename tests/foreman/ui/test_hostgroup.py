"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseComponent: HostGroup

:Team: Proton

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import DEFAULT_CV, ENVIRONMENT, RESOURCE_DEFAULT


@pytest.mark.e2e
def test_positive_end_to_end(session, module_org, module_location, module_target_sat):
    """Perform end to end testing for host group component

    :id: 537d95f2-fe32-4e06-a2cb-21c80fe8e2e2

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = module_target_sat.api.Architecture().create()
    os = module_target_sat.api.OperatingSystem(architecture=[architecture]).create()
    os_name = f'{os.name} {os.major}'
    domain = module_target_sat.api.Domain(
        organization=[module_org], location=[module_location]
    ).create()
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
        assert not module_target_sat.api.HostGroup().search(query={'search': f'name={new_name}'})


def test_negative_delete_with_discovery_rule(
    session, module_org, module_location, module_target_sat
):
    """Attempt to delete hostgroup which has dependent discovery rule

    :id: bd046e9a-f0d0-4110-8f94-fd04193cb3af

    :customerscenario: true

    :BZ: 1254102

    :expectedresults: Hostgroup was not deleted. Informative error message
        was shown

    :CaseImportance: High
    """
    hostgroup = module_target_sat.api.HostGroup(
        organization=[module_org], location=[module_location]
    ).create()
    module_target_sat.api.DiscoveryRule(
        hostgroup=hostgroup, organization=[module_org], location=[module_location]
    ).create()
    with session:
        assert session.hostgroup.search(hostgroup.name)[0]['Name'] == hostgroup.name
        # Make an attempt to delete host group that associated with discovery rule
        with pytest.raises(AssertionError) as context:
            session.hostgroup.delete(hostgroup.name)
        assert "Cannot delete record because dependent discovery rules exist" in str(context.value)
        assert session.hostgroup.search(hostgroup.name)[0]['Name'] == hostgroup.name


def test_create_with_config_group(module_puppet_org, module_puppet_loc, session_puppet_enabled_sat):
    """Create new host group with assigned config group to it

    :id: 05a64d6b-113b-4652-86bf-19bc65b70131

    :CaseImportance: Medium

    :expectedresults: Host group created and contains proper config group
    """
    name = gen_string('alpha')
    environment = session_puppet_enabled_sat.api.Environment(
        organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
    config_group = session_puppet_enabled_sat.api.ConfigGroup().create()
    with session_puppet_enabled_sat.ui_session() as session:
        # Create host group with config group
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        session.hostgroup.create(
            {
                'host_group.name': name,
                'host_group.puppet_environment': environment.name,
                'puppet_enc.config_groups.assigned': [config_group.name],
            }
        )
        hostgroup_values = session.hostgroup.read(name, widget_names='puppet_enc')
        assert len(hostgroup_values['puppet_enc']['config_groups']['assigned']) == 1
        assert hostgroup_values['puppet_enc']['config_groups']['assigned'][0] == config_group.name


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_create_with_puppet_class(module_puppet_org, module_puppet_loc, session_puppet_enabled_sat):
    """Create new host group with assigned puppet class to it

    :id: 166ca6a6-c0f7-4fa0-a3f2-b0d6980cf50d

    :CaseImportance: Medium

    :expectedresults: Host group created and contains proper puppet class
    """
    name = gen_string('alpha')
    pc_name = 'generic_1'
    env_name = session_puppet_enabled_sat.create_custom_environment(repo=pc_name)
    env = (
        session_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name={env_name}'})[0]
        .read()
    )
    env = session_puppet_enabled_sat.api.Environment(
        id=env.id,
        location=[module_puppet_loc],
        organization=[module_puppet_org],
    ).update(['location', 'organization'])
    env = session_puppet_enabled_sat.api.Environment(
        id=env.id, location=[module_puppet_loc]
    ).update(['location'])
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        # Create host group with puppet class
        session.hostgroup.create(
            {
                'host_group.name': name,
                'host_group.puppet_environment': env.name,
                'puppet_enc.classes.assigned': [pc_name],
            }
        )
        hostgroup_values = session.hostgroup.read(name, widget_names='puppet_enc')
        assert len(hostgroup_values['puppet_enc']['classes']['assigned']) == 1
        assert hostgroup_values['puppet_enc']['classes']['assigned'][0] == pc_name


@pytest.mark.stubbed
def test_positive_create_new_host():
    """Verify that content source field automatically populates when creating new host from host
    group.

    :id: 49704437-5ca1-46cb-b74e-de58396add37

    :steps:

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

    :steps:

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
                'activation_keys.activation_keys': module_ak_cv_lce.name,
            },
        )
        child_hostgroup_values = session.hostgroup.read(f'{parent_hg_name}/{child_hg_name}')
        assert parent_hg_name in child_hostgroup_values['host_group']['parent_name']
        assert module_lce.name in child_hostgroup_values['host_group']['lce']
        assert module_published_cv.name in child_hostgroup_values['host_group']['content_view']

        # Delete nested host group
        session.hostgroup.delete(f'{parent_hg_name}/{child_hg_name}')
        assert not target_sat.api.HostGroup().search(query={'search': f'name={child_hg_name}'})


def test_positive_clone_host_groups(
    session, module_org, module_lce, module_published_cv, module_ak_cv_lce, target_sat
):
    """Verify create, update and delete operation for clone host-group

    :id: 9f02dcc5-98aa-48bd-8114-edd3a0be65c1

    :steps:
        1. Create the host-group.
        2. Clone the host-group created in step 1
        3. Update and Delete the cloned host-group.

    :CaseImportance: High

    :expectedresults: Crud operations with cloned host-group should work as expected.

    :BZ: 2122261

    :BlockedBy: SAT-20435

    :customerscenario: true
    """
    parent_hg_name = gen_string('alpha')
    clone_hg_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = target_sat.api.Architecture().create()
    os = target_sat.api.OperatingSystem(architecture=[architecture]).create()
    os_name = f'{os.name} {os.major}'
    with session:
        # Create host-group with lce and content view
        session.hostgroup.create(
            {
                'host_group.name': parent_hg_name,
                'host_group.description': description,
                'host_group.lce': module_lce.name,
                'host_group.content_view': module_published_cv.name,
                'operating_system.architecture': architecture.name,
                'operating_system.operating_system': os_name,
                'activation_keys.activation_keys': module_ak_cv_lce.name,
            }
        )
        assert target_sat.api.HostGroup().search(query={'search': f'name={parent_hg_name}'})

        # Clone host group of name
        session.hostgroup.clone(
            parent_hg_name,
            {
                'host_group.name': clone_hg_name,
            },
        )
        assert target_sat.api.HostGroup().search(query={'search': f'name={clone_hg_name}'})
        clone_hostgroup_values = session.hostgroup.read(clone_hg_name)
        assert module_lce.name in clone_hostgroup_values['host_group']['lce']
        assert module_published_cv.name in clone_hostgroup_values['host_group']['content_view']
        assert (
            module_ak_cv_lce.name in clone_hostgroup_values['activation_keys']['ak_chip_group'][0]
        )
        assert os_name in clone_hostgroup_values['operating_system']['operating_system']
        assert architecture.name in clone_hostgroup_values['operating_system']['architecture']

        # Update clone host group
        session.hostgroup.update(
            clone_hg_name,
            {
                'host_group.lce': ENVIRONMENT,
                'host_group.content_view': DEFAULT_CV,
            },
        )
        clone_hostgroup_values = session.hostgroup.read(clone_hg_name)
        assert ENVIRONMENT in clone_hostgroup_values['host_group']['lce']
        assert DEFAULT_CV in clone_hostgroup_values['host_group']['content_view']

        # Delete parent and clone host group
        session.hostgroup.delete(parent_hg_name)
        assert target_sat.api.HostGroup().search(query={'search': f'name={clone_hg_name}'})
        session.hostgroup.delete(clone_hg_name)
        assert not target_sat.api.HostGroup().search(query={'search': f'name={clone_hg_name}'})


def test_positive_nested_host_group_compute_resource(
    module_target_sat, module_org, module_location, module_cr_libvirt
):
    """Verify that child host group can be created with option 'Deploy On = Bare Metal'
    if the parent group has set different compute resource/Deploy On value.

    :id: d3b5ed7a-083c-11f0-907b-000c29a0e355

    :Verifies: SAT-20579

    :steps:
        1. Create a host group with deployment on Libvirt compute resource.
        2. Create a nested host group and set the deployment on 'Bare Metal'.

    :expectedresults:
        Creation of nested host group with deployment on Bare Metal compute resource is successful.
    """
    parent_hg_name = gen_string('alpha')
    child_hg_name = gen_string('alpha')
    libvirt_cr_ui_name = f'{module_cr_libvirt.name} (Libvirt)'
    cr_bare_metal = RESOURCE_DEFAULT

    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        session.hostgroup.create(
            {
                'host_group.name': parent_hg_name,
                'host_group.deploy': libvirt_cr_ui_name,
            }
        )
        parent_hostgroup_values = session.hostgroup.read(parent_hg_name)
        assert parent_hostgroup_values['host_group']['deploy'] == libvirt_cr_ui_name
        session.hostgroup.create(
            {
                'host_group.parent_name': parent_hg_name,
                'host_group.name': child_hg_name,
                'host_group.deploy': cr_bare_metal,
            }
        )
        child_hostgroup_values = session.hostgroup.read(f'{parent_hg_name}/{child_hg_name}')
        assert child_hostgroup_values['host_group']['deploy'] == cr_bare_metal


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_nested_host_group_media_visible_with_synced_content(
    module_target_sat_in_org_and_loc,
    hostgroup_with_synced_ks,
    module_sca_manifest_org,
    module_location,
):
    """Verify that if user creates a child host group, created from a parent group with LCE & CV
    with synced kickstart repository, the "Media" drop-down on the "Operating System" tab is not visible
    and only the "Synced Content" drop-down is visible.

    :id: d118d24e-0f30-11f0-b6d3-000c29a0e355

    :Verifies: SAT-30138

    :setup:
        Create a parent host group with assigned lifecycle environment & content view
        with synced kickstart repository.

    :steps:
        1. Create a nested host group from the parent one in the setup.
        2. Check the "Operating System/Media Selection" radio button value.
        3. Check, if the "Operating System/Media" drop-down is visible.

    :expectedresults:
        2. The "Media Selection" radio button should be set to "Synced Content"
            and the "Synced Content" drop-down should be visible.
        3. The "Media" drop-down should not be visible.
    """
    parent_hg_name = hostgroup_with_synced_ks.name
    child_hg_name = gen_string('alpha')

    with module_target_sat_in_org_and_loc.ui_session() as session:
        session.organization.select(org_name=module_sca_manifest_org.name)
        session.location.select(loc_name=module_location.name)

        parent_hostgroup_values = session.hostgroup.read(parent_hg_name)
        assert parent_hostgroup_values['operating_system']['media_type'] == 'Synced Content'
        assert parent_hostgroup_values['operating_system']['media_content']['synced_content']

        session.hostgroup.create(
            {
                'host_group.parent_name': hostgroup_with_synced_ks.name,
                'host_group.name': child_hg_name,
            }
        )
        child_hostgroup_values = session.hostgroup.read(f'{parent_hg_name}/{child_hg_name}')
        assert child_hostgroup_values['operating_system']['media_type'] == 'Synced Content'
        assert child_hostgroup_values['operating_system']['media_content']['synced_content']
        assert not child_hostgroup_values['operating_system']['media_content'].get('media')
