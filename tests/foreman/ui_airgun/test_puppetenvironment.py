from pytest import raises
from nailgun import entities
import pytest
from robottelo.datafactory import (
    gen_string,
)
from robottelo.decorators import (
    tier1,
    upgrade,
    run_only_on,
)


@pytest.fixture(scope='module')
def fixture_for_puppet_environment():
    """Fixture returns values for new environment"""
    name = gen_string('alpha')
    org = entities.Organization().create()
    location = entities.Location().create()
    smartVariableValues = {
        'environment.name': name,
        'locations.locations.assigned': [location.name],
        'organizations.organizations.assigned': [org.name],
    }
    return smartVariableValues


@run_only_on('sat')
@tier1
def test_positive_create(session, fixture_for_puppet_environment):
    """
    Create new environment with name, location and organization

    :id: 663bc34e-df98-4c63-9184-abc3bf395475

    :expectedresults: Environment is created
    """
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        assert session.puppetenvironment.search(
            values.get('environment.name'))[0]['Name'] == \
            values.get('environment.name')
        env_values = session.puppetenvironment.read(
            values.get('environment.name'))
        assert env_values['locations']['locations']['assigned'][0] == \
            values.get('locations.locations.assigned')[0]


@run_only_on('sat')
@tier1
def test_negative_create(session):
    """
    Create a new environment with the bad format of the name

    :id: ef21c4f2-72e9-11e8-92c5-54e1ad07c9dd

    :expectedresults: Environment is not created

    :CaseImportance: Critical
    """
    name = ' '
    with session:
        session.puppetenvironment.create({'name': name})
        with raises(AssertionError):
            assert session.puppetenvironment.search(
                name)[0]['Name'] == name


@run_only_on('sat')
@tier1
def test_positive_update(session, fixture_for_puppet_environment):
    """
    Update environment with a new name

    :id: f3744a5e-2adc-448a-8e02-13d76121eea0

    :expectedresults: Environment is updated

    :CaseImportance: Critical
    """
    ak_name = gen_string('alpha')
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        session.puppetenvironment.update(values.get('environment.name'), {
            'environment.name': ak_name,
        })
        assert session.puppetenvironment.search(
            ak_name)[0]['Name'] == ak_name


@run_only_on('sat')
@tier1
@upgrade
def test_positive_delete(session, fixture_for_puppet_environment):
    """
    Delete an environment

    :id: 5869d9b5-fbb1-4e76-bbb7-9f536b717af0

    :expectedresults: Environment is deleted

    :CaseImportance: Critical
    """
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        session.puppetenvironment.delete(values.get('environment.name'))
        assert not session.puppetenvironment.search(
            values.get('environment.name'))
