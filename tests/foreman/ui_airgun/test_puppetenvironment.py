from nailgun import entities
import pytest
from robottelo.datafactory import (
    gen_string,
    invalid_values_list,
)


@pytest.fixture(scope='module')
def init_values():
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


def test_positive_create(session, init_values):
    name = init_values.get('environment.name')
    with session:
        session.puppetenvironment.create(values=init_values)
        assert session.puppetenvironment.search(
            name)[0]['Name'] == name
        env_values = session.puppetenvironment.read(name)
        assert env_values['locations']['resources']['assigned'][0] == \
            init_values.get('locations.resources.assigned')[0]


def test_negative_create(session):
    for name in invalid_values_list(interface='ui'):
        with session:
            session.puppetenvironment.create({'name': name})
            assert not session.puppetenvironment.search(name)


def test_positive_update(session, init_values):
    ak_name = gen_string('alpha')
    name = init_values.get('environment.name')
    with session:
        session.puppetenvironment.create(values=init_values)
        session.puppetenvironment.update(name, {
            'environment.name': ak_name,
        })
        assert session.puppetenvironment.search(
            ak_name)[0]['Name'] == ak_name


def test_positive_delete(session, init_values):
    name = init_values.get('environment.name')
    with session:
        session.puppetenvironment.create(values=init_values)
        session.puppetenvironment.delete(name)
        assert not session.puppetenvironment.search(name)
