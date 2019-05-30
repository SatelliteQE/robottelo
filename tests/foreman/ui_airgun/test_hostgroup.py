# -*- encoding: utf-8 -*-
"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseComponent: HostGroup

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, DEFAULT_CV, ENVIRONMENT
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@tier2
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for host group component

    :id: 537d95f2-fe32-4e06-a2cb-21c80fe8e2e2

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    architecture = entities.Architecture().create()
    os = entities.OperatingSystem(architecture=[architecture]).create()
    os_name = u'{0} {1}'.format(os.name, os.major)
    domain = entities.Domain(
        organization=[module_org], location=[module_loc]).create()
    with session:
        # Create host group with some data
        session.hostgroup.create({
            'host_group.name': name,
            'host_group.description': description,
            'host_group.lce': ENVIRONMENT,
            'host_group.content_view': DEFAULT_CV,
            'network.domain': domain.name,
            'operating_system.architecture': architecture.name,
            'operating_system.operating_system': os_name,
        })
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
        assert not session.hostgroup.search(new_name)


@tier2
def test_create_with_config_group(session, module_org, module_loc):
    """Create new host group with assigned config group to it

    :id: 05a64d6b-113b-4652-86bf-19bc65b70131

    :expectedresults: Host group created and contains proper config group

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    environment = entities.Environment(
        organization=[module_org], location=[module_loc]).create()
    config_group = entities.ConfigGroup().create()
    with session:
        # Create host group with config group
        session.hostgroup.create({
            'host_group.name': name,
            'host_group.puppet_environment': environment.name,
            'puppet_classes.config_groups.assigned': [config_group.name],
        })
        hostgroup_values = session.hostgroup.read(name, widget_names='puppet_classes')
        assert len(hostgroup_values['puppet_classes']['config_groups']['assigned']) == 1
        assert hostgroup_values[
            'puppet_classes']['config_groups']['assigned'][0] == config_group.name


@tier2
def test_create_with_puppet_class(session, module_org, module_loc):
    """Create new host group with assigned puppet class to it

    :id: 166ca6a6-c0f7-4fa0-a3f2-b0d6980cf50d

    :expectedresults: Host group created and contains proper puppet class

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    pc_name = 'generic_1'
    cv = publish_puppet_module(
        [{'author': 'robottelo', 'name': pc_name}],
        CUSTOM_PUPPET_REPO,
        organization_id=module_org.id
    )
    env = entities.Environment().search(query={
        'search': u'content_view="{0}" and organization_id={1}'.format(
            cv.name, module_org.id)})[0].read()
    env = entities.Environment(id=env.id, location=[module_loc]).update(['location'])
    with session:
        # Create host group with puppet class
        session.hostgroup.create({
            'host_group.name': name,
            'host_group.puppet_environment': env.name,
            'puppet_classes.classes.assigned': [pc_name],
        })
        hostgroup_values = session.hostgroup.read(name, widget_names='puppet_classes')
        assert len(hostgroup_values['puppet_classes']['classes']['assigned']) == 1
        assert hostgroup_values[
            'puppet_classes']['classes']['assigned'][0] == pc_name
