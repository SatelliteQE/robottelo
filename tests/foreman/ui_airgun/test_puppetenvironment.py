from pytest import raises
from nailgun import entities
import pytest
from robottelo.datafactory import (
    gen_string,
)
from robottelo.decorators import (
    tier2,
    run_only_on,
)


@pytest.fixture(scope='module')
def fixture_for_puppet_environment():
    """Fixture returns values for new environment"""
    name = gen_string('alpha')
    org = entities.Organization().create()
    location = entities.Location().create()
    puppetEnvironmentValues = {
        'environment.name': name,
        'locations.resources.assigned': [location.name],
        'organizations.resources.assigned': [org.name],
    }
    return puppetEnvironmentValues


def test_positive_create(session, fixture_for_puppet_environment):
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        assert session.puppetenvironment.search(
            values.get('environment.name'))[0]['Name'] == \
            values.get('environment.name')
        env_values = session.puppetenvironment.read(
            values.get('environment.name'))
        assert env_values['locations']['resources']['assigned'][0] == \
            values.get('locations.resources.assigned')[0]


def test_negative_create(session):
    name = ' '
    with session:
        session.puppetenvironment.create({'name': name})
        with raises(AssertionError):
            assert session.puppetenvironment.search(
                name)[0]['Name'] == name


def test_positive_update(session, fixture_for_puppet_environment):
    ak_name = gen_string('alpha')
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        session.puppetenvironment.update(values.get('environment.name'), {
            'environment.name': ak_name,
        })
        assert session.puppetenvironment.search(
            ak_name)[0]['Name'] == ak_name


def test_positive_delete(session, fixture_for_puppet_environment):
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        session.puppetenvironment.delete(values.get('environment.name'))
        assert not session.puppetenvironment.search(
            values.get('environment.name'))


@run_only_on('sat')
@tier2
def test_positive_availability_for_hostgroup_in_multiple_orgs(
        session, fixture_for_puppet_environment):
    """
    New environment that present in different organizations should be
    visible for any created hostgroup in these organizations

    :id: c086f0c4-3cef-4b58-95aa-40d89954138b

    :customerscenario: true

    :expectedresults: Environment can be used for any new hostgroup and any
        organization where it is present in

    :BZ: 543178

    :CaseLevel: Integration

    :CaseImportance: High
    """
    values = fixture_for_puppet_environment
    with session:
        session.puppetenvironment.create(values=values)
        env_name = values.get('environment.name')
        session.puppetenvironment.search_environment({
            'hostgroup.puppet_environment': env_name,
        })
