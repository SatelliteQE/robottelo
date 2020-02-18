"""Test class for Config Groups UI

:Requirement: Config Group

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ConfigurationManagement

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.decorators import fixture
from robottelo.decorators import tier2
from robottelo.decorators import upgrade


@fixture(scope='module')
def module_puppet_class():
    return entities.PuppetClass().create()


@tier2
@upgrade
def test_positive_end_to_end(session, module_puppet_class):
    """Perform end to end testing for config group component

    :id: 3ac47175-1239-4481-9ae2-e31980fb6607

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        # Create new config group
        session.configgroup.create({'name': name, 'classes.assigned': [module_puppet_class.name]})
        assert session.configgroup.search(name)[0]['Name'] == name
        values = session.configgroup.read(name)
        assert values['name'] == name
        assert len(values['classes']['assigned']) == 1
        assert values['classes']['assigned'][0] == module_puppet_class.name
        # Update config group with new name
        session.configgroup.update(name, {'name': new_name})
        assert session.configgroup.search(new_name)[0]['Name'] == new_name
        assert not session.configgroup.search(name)
        # Delete config group
        session.configgroup.delete(new_name)
        assert not session.configgroup.search(new_name)
