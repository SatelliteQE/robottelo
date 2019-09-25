"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from nailgun import entities
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT, OSCAP_PROFILE
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier1, tier2, upgrade
from robottelo.helpers import file_downloader
from robottelo import ssh


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc(module_org):
    return entities.Location(organization=[module_org]).create()


@fixture(scope='module')
def module_host_group(module_loc, module_org):
    return entities.HostGroup(
        location=[module_loc],
        organization=[module_org],
    ).create()


@fixture(scope='module')
def oscap_content_path():
    # download scap content from satellite
    _, file_name = os.path.split(settings.oscap.content_path)
    local_file = "/tmp/{}".format(file_name)
    ssh.download_file(settings.oscap.content_path, local_file)
    return local_file


@fixture(scope='module')
def oscap_tailoring_path():
    return file_downloader(settings.oscap.tailoring_path)[0]


@tier2
def test_positive_check_dashboard(
        session, module_host_group, module_loc,
        module_org, oscap_content_path):
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

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    oscap_content_title = gen_string('alpha')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    content_view = entities.ContentView(organization=module_org).create()
    content_view.publish()
    content_view = content_view.read()
    promote(content_view.version[0], environment_id=lce.id)
    entities.Host(
        hostgroup=module_host_group,
        location=module_loc,
        organization=module_org,
        content_facet_attributes={
            'content_view_id': content_view.id,
            'lifecycle_environment_id': lce.id,
        },
    ).create()
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        session.location.select(loc_name=ANY_CONTEXT['location'])
        session.oscapcontent.create({
            'file_upload.title': oscap_content_title,
            'file_upload.scap_file': oscap_content_path,
        })
        session.oscappolicy.create({
            'create_policy.name': name,
            'scap_content.scap_content_resource': oscap_content_title,
            'scap_content.xccdf_profile': OSCAP_PROFILE['security7'],
            'schedule.period': 'Weekly',
            'schedule.period_selection.weekday': 'Friday',
            'locations.resources.assigned': [module_loc.name],
            'organizations.resources.assigned': [module_org.name],
            'host_group.resources.assigned': [module_host_group.name]
        })
        policy_details = session.oscappolicy.details(name)
        assert policy_details['HostsBreakdownStatus']['total_count'] == 1
        host_breakdown_chart = policy_details[
            'HostBreakdownChart']['hosts_breakdown'].split(" ", 1)
        assert host_breakdown_chart[0] == '100%'
        assert host_breakdown_chart[1] == 'Not audited'


@tier1
@upgrade
def test_positive_end_to_end(
        session, module_host_group, module_loc, module_org,
        oscap_content_path, oscap_tailoring_path):
    """Perform end to end testing for oscap policy component

    :id: 39c26f89-3147-4f27-bf5e-810f0ba721d8

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = '{} {}'.format(gen_string('alpha'), gen_string('alpha'))
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    oscap_content_title = gen_string('alpha')
    tailoring_name = gen_string('alpha')
    profile_type = OSCAP_PROFILE['security7']
    tailoring_type = OSCAP_PROFILE['tailoring_rhel7']
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        session.location.select(loc_name=ANY_CONTEXT['location'])
        # Upload oscap content to the application
        session.oscapcontent.create({
            'file_upload.title': oscap_content_title,
            'file_upload.scap_file': oscap_content_path,
        })
        # Upload tailoring file to the application
        session.oscaptailoringfile.create({
            'file_upload.name': tailoring_name,
            'file_upload.scap_file': oscap_tailoring_path,
        })
        # Create new oscap policy with assigned content and tailoring file
        session.oscappolicy.create({
            'create_policy.name': name,
            'create_policy.description': description,
            'scap_content.scap_content_resource': oscap_content_title,
            'scap_content.xccdf_profile': profile_type,
            'scap_content.tailoring_file': tailoring_name,
            'scap_content.xccdf_profile_tailoring_file': tailoring_type,
            'schedule.period': 'Monthly',
            'schedule.period_selection.day_of_month': '5',
            'locations.resources.assigned': [module_loc.name],
            'organizations.resources.assigned': [module_org.name],
            'host_group.resources.assigned': [module_host_group.name]
        })
        assert session.oscappolicy.search(name)[0]['Name'] == name
        # Check that created entity has expected values
        oscappolicy_values = session.oscappolicy.read(name)
        assert oscappolicy_values['general']['name'] == name
        assert oscappolicy_values['general']['description'] == description
        assert oscappolicy_values['scap_content']['scap_content'] == oscap_content_title
        assert oscappolicy_values['scap_content']['xccdf_profile'] == profile_type
        assert oscappolicy_values['scap_content']['tailoring_file'] == tailoring_name
        assert oscappolicy_values[
            'scap_content']['xccdf_profile_tailoring_file'] == tailoring_type
        assert oscappolicy_values['schedule']['period'] == 'Monthly'
        assert oscappolicy_values['schedule']['period_selection']['day_of_month'] == '5'
        assert module_loc.name in oscappolicy_values['locations']['resources']['assigned']
        assert module_org.name in oscappolicy_values['organizations']['resources']['assigned']
        assert oscappolicy_values[
            'host_group']['resources']['assigned'] == [module_host_group.name]
        # Update oscap policy with new name
        session.oscappolicy.update(name, {'general.name': new_name})
        assert session.oscappolicy.search(new_name)[0]['Name'] == new_name
        assert not session.oscappolicy.search(name)
        # Delete oscap policy entity
        session.oscappolicy.delete(new_name)
        assert not session.oscappolicy.search(new_name)
