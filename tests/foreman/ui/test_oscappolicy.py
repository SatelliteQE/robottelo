"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.constants import OSCAP_PROFILE
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_host_group(default_location, default_org):
    return entities.HostGroup(location=[default_location], organization=[default_org]).create()


@pytest.mark.tier2
def test_positive_check_dashboard(
    session,
    module_host_group,
    default_location,
    default_org,
    oscap_content_path,
    import_ansible_roles,
):
    """Create OpenScap Policy which is connected to the host. That policy
    dashboard should be rendered and correctly display information about
    the host

    :id: 3c1575cb-f290-4d99-bb86-61b9ca6a62eb

    :customerscenario: true

    :Steps:

        1. Create new host group
        2. Create new host using host group from step 1
        3. Create an openscap content.
        4. Create an openscap Policy using host group from step 1

    :expectedresults: Policy dashboard rendered properly and has necessary
        data

    :BZ: 1424936

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    oscap_content_title = gen_string('alpha')
    lce = entities.LifecycleEnvironment(organization=default_org).create()
    content_view = entities.ContentView(organization=default_org).create()
    content_view.publish()
    content_view = content_view.read()
    promote(content_view.version[0], environment_id=lce.id)
    entities.Host(
        hostgroup=module_host_group,
        location=default_location,
        organization=default_org,
        content_facet_attributes={
            'content_view_id': content_view.id,
            'lifecycle_environment_id': lce.id,
        },
    ).create()
    entities.ScapContents(
        title=oscap_content_title,
        scap_file=oscap_content_path,
        organization=[default_org],
        location=[default_location],
    ).create()
    with session:
        session.organization.select(org_name=default_org.name)
        session.location.select(loc_name=default_location.name)
        session.oscappolicy.create(
            {
                'deployment_options.deploy_by': 'ansible',
                'policy_attributes.name': name,
                'scap_content.scap_content_resource': oscap_content_title,
                'scap_content.xccdf_profile': OSCAP_PROFILE['security7'],
                'schedule.period': 'Weekly',
                'schedule.period_selection.weekday': 'Friday',
                'locations.resources.assigned': [default_location.name],
                'organizations.resources.assigned': [default_org.name],
                'host_group.resources.assigned': [module_host_group.name],
            }
        )
        policy_details = session.oscappolicy.details(name)
        assert policy_details['HostsBreakdownStatus']['total_count'] == 1
        # Skipping this assertion for now because of some UI changes.
        # assert policy_details['HostBreakdownChart']['hosts_breakdown'] == '100%Not audited'


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_end_to_end(
    session,
    module_host_group,
    default_location,
    default_org,
    oscap_content_path,
    tailoring_file_path,
    import_ansible_roles,
):
    """Perform end to end testing for oscap policy component

    :id: 39c26f89-3147-4f27-bf5e-810f0ba721d8

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    name = '{} {}'.format(gen_string('alpha'), gen_string('alpha'))
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    oscap_content_title = gen_string('alpha')
    tailoring_name = gen_string('alpha')
    profile_type = OSCAP_PROFILE['security7']
    tailoring_type = OSCAP_PROFILE['tailoring_rhel7']
    # Upload oscap content file
    entities.ScapContents(
        title=oscap_content_title,
        scap_file=oscap_content_path,
        organization=[default_org],
        location=[default_location],
    ).create()
    # Upload tailoring file
    entities.TailoringFile(
        name=tailoring_name,
        scap_file=tailoring_file_path['local'],
        organization=[default_org],
        location=[default_location],
    ).create()
    with session:
        session.organization.select(org_name=default_org.name)
        session.location.select(loc_name=default_location.name)
        # Create new oscap policy with assigned content and tailoring file
        session.oscappolicy.create(
            {
                'deployment_options.deploy_by': 'ansible',
                'policy_attributes.name': name,
                'policy_attributes.description': description,
                'scap_content.scap_content_resource': oscap_content_title,
                'scap_content.xccdf_profile': profile_type,
                'scap_content.tailoring_file': tailoring_name,
                'scap_content.xccdf_profile_tailoring_file': tailoring_type,
                'schedule.period': 'Monthly',
                'schedule.period_selection.day_of_month': '5',
                'locations.resources.assigned': [default_location.name],
                'organizations.resources.assigned': [default_org.name],
                'host_group.resources.assigned': [module_host_group.name],
            }
        )
        assert session.oscappolicy.search(name)[0]['Name'] == name
        # Check that created entity has expected values
        oscappolicy_values = session.oscappolicy.read(name)
        assert oscappolicy_values['deployment_options']['deploy_by'] == 'ansible'
        assert oscappolicy_values['general']['name'] == name
        assert oscappolicy_values['general']['description'] == description
        assert oscappolicy_values['scap_content']['scap_content'] == oscap_content_title
        assert oscappolicy_values['scap_content']['xccdf_profile'] == profile_type
        assert oscappolicy_values['scap_content']['tailoring_file'] == tailoring_name
        assert oscappolicy_values['scap_content']['xccdf_profile_tailoring_file'] == tailoring_type
        assert oscappolicy_values['schedule']['period'] == 'Monthly'
        assert oscappolicy_values['schedule']['period_selection']['day_of_month'] == '5'
        assert default_location.name in oscappolicy_values['locations']['resources']['assigned']
        assert default_org.name in oscappolicy_values['organizations']['resources']['assigned']
        assert oscappolicy_values['host_group']['resources']['assigned'] == [module_host_group.name]
        # Update oscap policy with new name
        session.oscappolicy.update(name, {'general.name': new_name})
        oscappolicy_values = session.oscappolicy.read(new_name)
        assert oscappolicy_values['general']['name'] == new_name
        assert not session.oscappolicy.search(name)
        # Delete oscap policy entity
        session.oscappolicy.delete(new_name)
        assert not session.oscappolicy.search(new_name)
