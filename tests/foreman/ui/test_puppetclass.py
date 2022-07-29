"""Test class for Puppet Classes UI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
import pytest
from fauxfactory import gen_string


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session_puppet_enabled_sat, module_puppet_org, module_puppet_loc):
    """Perform end to end testing for puppet class component

    :id: f837eec0-101c-4aff-a270-652005bdee51

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    hostgroup = session_puppet_enabled_sat.api.HostGroup(
        organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
    puppet_class = session_puppet_enabled_sat.api.PuppetClass(name=name).create()
    with session_puppet_enabled_sat.ui_session() as session:
        session.organization.select(org_name=module_puppet_org.name)
        # Check that created puppet class can be found in UI
        assert session.puppetclass.search(name)[0]['Class name'] == name
        # Read puppet class values and check that they are expected
        pc_values = session.puppetclass.read(name)
        assert pc_values['puppet_class']['name'] == name
        assert not pc_values['puppet_class']['puppet_environment']
        assert not pc_values['puppet_class']['host_group']['assigned']
        # Update puppet class
        session.puppetclass.update(
            puppet_class.name, {'puppet_class.host_group.assigned': [hostgroup.name]}
        )
        pc_values = session.puppetclass.read(name)
        assert pc_values['puppet_class']['host_group']['assigned'] == [hostgroup.name]
        # Make an attempt to delete puppet class that associated with host group
        with pytest.raises(AssertionError) as context:
            session.puppetclass.delete(name)
        assert f'{puppet_class.name} is used by {hostgroup.name}' in str(context.value)
        # Unassign puppet class from host group
        session.puppetclass.update(
            puppet_class.name, {'puppet_class.host_group.unassigned': [hostgroup.name]}
        )
        # Delete puppet class
        session.puppetclass.delete(name)
        assert not session.puppetclass.search(name)
