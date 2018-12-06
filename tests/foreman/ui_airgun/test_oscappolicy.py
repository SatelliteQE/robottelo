"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2


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
    return settings.oscap.content_path


@fixture(scope='module')
def oscap_tailoring_path():
    return settings.oscap.tailoring_path


@tier2
def test_positive_check_dashboard(session, module_host_group, module_loc,
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
        session.oscapcontent.create({
            'file_upload.title': oscap_content_title,
            'file_upload.scap_file': oscap_content_path,
        })
        session.oscappolicy.create({
            'create_policy.name': name,
            'scap_content.scap_content_resource': oscap_content_title,
            'scap_content.xccdf_profile': 'C2S for Red Hat Enterprise Linux 6',
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
