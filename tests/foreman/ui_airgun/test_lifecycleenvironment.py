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
        session.lce.create_environment_path(
            values={'name': lce_path_name}
        )
        session.lce.create_environment(
            entity_name=lce_path_name,
            values={'name': lce_name}
        )
        lce_values = session.lce.read()
        assert lce_name in lce_values['LCE']
        assert lce_path_name in lce_values['LCE'][lce_name]
