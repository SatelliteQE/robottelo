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
    valid_domain_names
)
from robottelo.decorators import (
    parametrize,
    tier2,
)


@pytest.fixture
def valid_domain_name():
    return list(valid_domain_names(interface='ui')['argvalues'])[0]


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
