"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html


:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:Team: Rocket

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.utils.datafactory import invalid_environments_list
from robottelo.utils.datafactory import invalid_names_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_environments_list


@pytest.mark.e2e
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_CRUD_with_attributes(
    session_puppet_enabled_sat, module_puppet_org, module_puppet_loc
):
    """Check if Environment with attributes can be created, updated and removed

    :id: d2187971-86b2-40c9-a93c-66f37691ae2c

    :BZ: 1337947

    :expectedresults:
        1. Environment is created and has parameters assigned
        2. Environment can be listed by parameters
        3. Environment can be updated
        4. Environment can be removed
    """
    puppet_sat = session_puppet_enabled_sat
    # Create with attributes
    env_name = gen_string('alpha')
    environment = puppet_sat.api.Environment(
        name=env_name, organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
    assert env_name == environment.name
    assert len(environment.organization) == 1
    assert environment.organization[0].id == module_puppet_org.id
    assert len(environment.location) == 1
    assert environment.location[0].id == module_puppet_loc.id

    # List by name
    envs = puppet_sat.api.Environment().search(query=dict(search=f'name={env_name}'))
    assert len(envs) == 1
    assert envs[0].name == env_name

    # List by org loc id
    envs = puppet_sat.api.Environment().search(
        query=dict(
            search=f'organization_id={module_puppet_org.id} and location_id={module_puppet_loc.id}'
        )
    )
    assert env_name in [res.name for res in envs]

    # List by org loc name
    envs = puppet_sat.api.Environment().search(
        query=dict(
            search=f'organization={module_puppet_org.name} and location={module_puppet_loc.name}'
        )
    )
    assert env_name in [res.name for res in envs]

    # Update org and loc
    new_org = puppet_sat.api.Organization().create()
    new_loc = puppet_sat.api.Location().create()
    new_env_name = gen_string('alpha')
    env = puppet_sat.api.Environment(
        id=environment.id, name=new_env_name, organization=[new_org], location=[new_loc]
    ).update(['name', 'organization', 'location'])
    assert len(env.organization) == 1
    assert env.organization[0].id == new_org.id
    assert env.organization[0].id != module_puppet_org.id
    assert len(env.location) == 1
    assert env.location[0].id == new_loc.id
    assert env.location[0].id != module_puppet_loc.id
    assert env.name == new_env_name

    # Delete
    environment.delete()
    with pytest.raises(HTTPError):
        environment.read()


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_environments_list()))
def test_positive_create_with_name(name, session_puppet_enabled_sat):
    """Create an environment and provide a valid name.

    :id: 8869ccf8-a511-4fa7-ac36-11494e85f532

    :parametrized: yes

    :expectedresults: The environment created successfully and has expected name
    """
    env = session_puppet_enabled_sat.api.Environment(name=name).create()
    assert env.name == name


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
def test_negative_create_with_too_long_name(name, session_puppet_enabled_sat):
    """Create an environment and provide an invalid name.

    :id: e2654954-b3a1-4594-a487-bcd0cc8195ad

    :parametrized: yes

    :expectedresults: The server returns an error.
    """
    with pytest.raises(HTTPError):
        session_puppet_enabled_sat.api.Environment(name=name).create()


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_environments_list()))
def test_negative_create_with_invalid_characters(name, session_puppet_enabled_sat):
    """Create an environment and provide an illegal name.

    :id: 8ec57d04-4ce6-48b4-b7f9-79025019ad0f

    :parametrized: yes

    :expectedresults: The server returns an error.
    """
    with pytest.raises(HTTPError):
        session_puppet_enabled_sat.api.Environment(name=name).create()


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(valid_environments_list()))
def test_positive_update_name(module_puppet_environment, new_name, session_puppet_enabled_sat):
    """Create environment entity providing the initial name, then
    update its name to another valid name.

    :id: ef48e79a-6b6a-4811-b49b-09f2effdd18f

    :parametrized: yes

    :expectedresults: Environment entity is created and updated properly
    """
    env = session_puppet_enabled_sat.api.Environment(
        id=module_puppet_environment.id, name=new_name
    ).update(['name'])
    assert env.name == new_name


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(invalid_names_list()))
def test_negative_update_name(module_puppet_environment, new_name, session_puppet_enabled_sat):
    """Create environment entity providing the initial name, then
    try to update its name to invalid one.

    :id: 9cd024ab-db3d-4b15-b6da-dd2089321df3

    :parametrized: yes

    :expectedresults: Environment entity is not updated
    """
    with pytest.raises(HTTPError):
        session_puppet_enabled_sat.api.Environment(
            id=module_puppet_environment.id, name=new_name
        ).update(['name'])


"""Tests to see if the server returns the attributes it should.

Satellite should return a full description of an entity each time an entity
is created, read or updated. These tests verify that certain attributes
really are returned. The ``one_to_*_names`` functions know what names
Satellite may assign to fields.

"""


@pytest.mark.tier2
def test_positive_update_loc(module_puppet_environment):
    """Update an environment. Inspect the server's response.

    :id: a4c1bc22-d586-4150-92fc-7797f0f5bfb0

    :expectedresults: The response contains some value for the ``location``
        field.

    :BZ: 1262029

    :CaseLevel: Integration
    """
    names = {'location', 'location_ids', 'locations'}
    attributes = set(module_puppet_environment.update_json([]).keys())
    assert len(names & attributes) >= 1, f'None of {names} are in {attributes}'


@pytest.mark.tier2
def test_positive_update_org(module_puppet_environment):
    """Update an environment. Inspect the server's response.

    :id: ac46bcac-5db0-4899-b2fc-d48d2116287e

    :expectedresults: The response contains some value for the
        ``organization`` field.

    :BZ: 1262029

    :CaseLevel: Integration
    """
    names = {'organization', 'organization_ids', 'organizations'}
    attributes = set(module_puppet_environment.update_json([]).keys())
    assert len(names & attributes) >= 1, f'None of {names} are in {attributes}'
