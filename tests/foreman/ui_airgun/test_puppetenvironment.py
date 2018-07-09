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
