"""Test class for Lifecycle Environment UI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities


from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


def test_positive_edit(session):
    lce_path_name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        session.lifecycleenvironment.create(
            values={'name': lce_path_name}
        )
        session.lifecycleenvironment.update(
            values={'details.name': new_name},
            entity_name=lce_path_name,
        )
        lce_values = session.lifecycleenvironment.read()
        assert new_name in lce_values['lce']


@tier2
def test_positive_create_chain(session):
    """Create Content Environment in a chain

    :id: ed3d2c88-ef0a-4a1a-9f11-5bdb2119fc18

    :expectedresults: Environment is created

    :CaseLevel: Integration
    """
    lce_path_name = gen_string('alpha')
    lce_name = gen_string('alpha')
    with session:
        session.lifecycleenvironment.create(
            values={'name': lce_path_name}
        )
        session.lifecycleenvironment.create(
            values={'name': lce_name},
            prior_entity_name=lce_path_name,
        )
        lce_values = session.lifecycleenvironment.read()
        assert lce_name in lce_values['lce']
        assert lce_path_name in lce_values['lce'][lce_name]
