# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes UI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import raises

from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc(module_org):
    return entities.Location(organization=[module_org]).create()


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for puppet class component

    :id: f837eec0-101c-4aff-a270-652005bdee51

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    variable_name = gen_string('alpha')
    name = gen_string('alpha')
    hostgroup = entities.HostGroup(
        organization=[module_org], location=[module_loc]).create()
    puppet_class = entities.PuppetClass(name=name).create()
    entities.SmartVariable(variable=variable_name, puppetclass=puppet_class).create()
    with session:
        # Check that created puppet class can be found in UI
        assert session.puppetclass.search(name)[0]['Class name'] == name
        # Read puppet class values and check that they are expected
        pc_values = session.puppetclass.read(name)
        assert pc_values['puppet_class']['name'] == name
        assert not pc_values['puppet_class']['puppet_environment']
        assert not pc_values['puppet_class']['host_group']['assigned']
        assert pc_values['smart_variables']['variable']['key'] == variable_name
        # Update puppet class
        session.puppetclass.update(
            puppet_class.name,
            {'puppet_class.host_group.assigned': [hostgroup.name]}
        )
        pc_values = session.puppetclass.read(name)
        assert pc_values['puppet_class']['host_group']['assigned'] == [hostgroup.name]
        # Make an attempt to delete puppet class that associated with host group
        with raises(AssertionError) as context:
            session.puppetclass.delete(name)
        assert "error: '{} is used by {}'".format(
            puppet_class.name, hostgroup.name) in str(context.value)
        # Unassign puppet class from host group
        session.puppetclass.update(
            puppet_class.name,
            {'puppet_class.host_group.unassigned': [hostgroup.name]}
        )
        # Delete puppet class
        session.puppetclass.delete(name)
        assert not session.puppetclass.search(name)
