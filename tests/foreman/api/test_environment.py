"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html


:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.api.utils import one_to_many_names
from robottelo.datafactory import invalid_environments_list
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_environments_list


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_environments_list()))
def test_positive_create_with_name(name, session_puppet_enabled_sat):
    """Create an environment and provide a valid name.

    :id: 8869ccf8-a511-4fa7-ac36-11494e85f532

    :parametrized: yes

    :expectedresults: The environment created successfully and has expected
        name.

    :CaseImportance: Critical
    """
    env = session_puppet_enabled_sat.api.Environment(name=name).create()
    assert env.name == name


@pytest.mark.tier1
def test_positive_create_with_org_and_loc(
    module_puppet_org, module_puppet_loc, session_puppet_enabled_sat
):
    """Create an environment and assign it to new organization.

    :id: de7e4132-5ca7-4b41-9af3-df075d31f8f4

    :expectedresults: The environment created successfully and has expected
        attributes.

    :CaseImportance: Critical
    """
    env = session_puppet_enabled_sat.api.Environment(
        name=gen_string('alphanumeric'),
        organization=[module_puppet_org],
        location=[module_puppet_loc],
    ).create()
    assert len(env.organization) == 1
    assert env.organization[0].id == module_puppet_org.id
    assert len(env.location) == 1
    assert env.location[0].id == module_puppet_loc.id


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


@pytest.mark.tier2
def test_positive_update_and_remove(
    module_puppet_org, module_puppet_loc, session_puppet_enabled_sat
):
    """Update environment and assign it to a new organization
    and location. Delete environment afterwards.

    :id: 31e43faa-65ee-4757-ac3d-3825eba37ae5

    :expectedresults: Environment entity is updated and removed
        properly

    :CaseImportance: Critical

    :CaseLevel: Integration
    """
    env = session_puppet_enabled_sat.api.Environment().create()
    assert len(env.organization) == 0
    assert len(env.location) == 0
    env = session_puppet_enabled_sat.api.Environment(
        id=env.id, organization=[module_puppet_org]
    ).update(['organization'])
    assert len(env.organization) == 1
    assert env.organization[0].id, module_puppet_org.id

    env = session_puppet_enabled_sat.api.Environment(
        id=env.id, location=[module_puppet_loc]
    ).update(['location'])
    assert len(env.location) == 1
    assert env.location[0].id == module_puppet_loc.id

    env.delete()
    with pytest.raises(HTTPError):
        env.read()


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
    names = one_to_many_names('location')
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
    names = one_to_many_names('organization')
    attributes = set(module_puppet_environment.update_json([]).keys())
    assert len(names & attributes) >= 1, f'None of {names} are in {attributes}'
