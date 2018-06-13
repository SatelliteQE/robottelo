# -*- encoding: utf-8 -*-
"""Test class for Domain UI

:Requirement: Domain

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
import pytest

from robottelo.datafactory import (
    invalid_domain_names,
    valid_domain_names
)
from robottelo.decorators import (
    parametrize,
    tier2,
    upgrade
)


@pytest.fixture
def valid_domain_name():
    return valid_domain_names(interface=None)[0]


@parametrize('name', **valid_domain_names(interface='ui', length=243))
def test_positive_create_with_name(session, name):
    """Create a new domain with name of 255 chars

    :id: 6366fa30-c94f-4d98-9c7f-c590e709cf79

    :expectedresults: Domain is created

    :CaseImportance: Critical
    """
    with session:
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        assert session.domain.search(name), (
            "Unable to find domain '{}' after creating"
            .format(name)
        )


@upgrade
def test_positive_delete(session, valid_domain_name):
    """Delete a domain

    :id: e05ec510-dfb0-4669-9371-7e594333d80c

    :expectedresults: Domain is deleted

    :CaseImportance: Critical
    """
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        session.domain.delete(name)
        assert not session.domain.search(name), (
            "Deleted domain '{}' still exists in UI"
            .format(name)
        )


@upgrade
@parametrize('new_name', **valid_domain_names(interface='ui'))
def test_positive_update(session, valid_domain_name, new_name):
    """Update a domain with name and description

    :id: 4a883383-da9c-4b03-bcb8-e1ffb203d19b

    :expectedresults: Domain is updated

    :CaseImportance: Critical
    """
    with session:
        old_name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': old_name,
            'domain.full_name': old_name,
        })
        session.domain.update(old_name, {'domain.dns_domain': new_name})
        assert session.domain.search(new_name), (
            "Unable to find domain '{}' after changing name (old name: {})"
            .format(new_name, old_name)
        )


@parametrize('name', **invalid_domain_names(interface='ui'))
def test_negative_create_with_invalid_name(session, name):
    """Try to create domain and use whitespace, blank, tab symbol or
    too long string of different types as its name value

    :id: 33c96cb6-711e-4a17-bce8-55e33ebcd342

    :expectedresults: Domain is not created

    :CaseImportance: Critical
    """
    with session:
        with pytest.raises(AssertionError) as context:
            session.domain.create({
                'domain.dns_domain': name,
                'domain.full_name': name,
            })
        assert 'errors present' in str(context.value)


@tier2
@parametrize('param_value', [gen_string('alpha', 255), ''],
             ids=['long_value', 'blank_value'])
def test_positive_set_parameter(session, valid_domain_name, param_value):
    """Set parameter in a domain with a value of 255 chars, or a blank value.

    :id: b346ae66-1720-46af-b0da-460c52ce9476

    :expectedresults: Domain parameter is created.

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha', 255)
    new_param = {'name': param_name, 'value': param_value}
    update_values = {'parameters.params': [new_param]}
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        session.domain.update(name, update_values)
        read_values = session.domain.read(name)
    assert read_values['parameters']['params'] == [new_param], (
        "Current domain parameters do not match expected value"
    )


@tier2
def test_negative_set_parameter(session, valid_domain_name):
    """Set a parameter in a domain with 256 chars in name and value.

    :id: 1c647d66-6a3f-4d88-8e6b-60f2fc7fd603

    :expectedresults: Domain parameter is not updated. Error is raised

    :CaseLevel: Integration
    """
    update_values = {
        'parameters.params': [
            {
                'name': gen_string('alpha', 256),
                'value': gen_string('alpha', 256)
            }
        ]
    }
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        with pytest.raises(AssertionError) as context:
            session.domain.update(name, update_values)
        assert 'Name is too long' in str(context.value)


@tier2
def test_negative_set_parameter_same(session, valid_domain_name):
    """Again set the same parameter for domain with name and value.

    :id: 6266f12e-cf94-4564-ba26-b467ced2737f

    :expectedresults: Domain parameter with same values is not created.

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        session.domain.add_parameter(name, param_name, param_value)
        with pytest.raises(AssertionError) as context:
            session.domain.add_parameter(name, param_name, param_value)
        assert 'Name has already been taken' in str(context.value)


@tier2
def test_positive_remove_parameter(session, valid_domain_name):
    """Remove a selected domain parameter

    :id: 8f7f8501-cf39-418f-a412-1a4b53698bc3

    :expectedresults: Domain parameter is removed

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        session.domain.add_parameter(name, param_name, param_value)
        session.domain.remove_parameter(name, param_name)
        params = session.domain.read(name)['parameters']['params']
        assert param_name not in [param['name'] for param in params]
