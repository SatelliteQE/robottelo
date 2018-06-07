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
from fauxfactory import gen_string, gen_utf8
import pytest

from robottelo.constants import DOMAIN
from robottelo.datafactory import parametrized
from robottelo.decorators import (
    parametrize,
    run_only_on,
    tier1,
    tier2,
    upgrade
)


def valid_domain_names(length=5):
    """Returns pytest parametrize kwargs for valid domain names."""
    max_len = 255 - len(DOMAIN % '')
    if max_len - length < 0:
        raise ValueError("length is too large, max: {}".format(max_len))
    names = {
        'alphanumeric': DOMAIN % gen_string('alphanumeric', length),
        'alpha': DOMAIN % gen_string('alpha', length),
        'numeric': DOMAIN % gen_string('numeric', length),
        'latin1': DOMAIN % gen_string('latin1', length),
        'utf8': DOMAIN % gen_utf8(length, smp=False),
    }
    return parametrized(names)


def invalid_domain_names():
    """Returns pytest parametrize kwargs for invalid names."""
    names = {
        'empty': '\0',
        'whitespace': ' ',
        'tab': '\t',
        'toolong': gen_string('alphanumeric', 300)
    }
    return parametrized(names)


def _create_domain(session, name=None, assert_created=True):
    """
    Create a domain and optionally assert that it is created
    """
    if not name:
        name = DOMAIN % gen_string('alpha')
    session.domain.create({
        'domain.dns_domain': name,
        'domain.full_name': name,
    })
    if assert_created:
        assert session.domain.search(name), (
            "Unable to find domain '{}' after creating"
            .format(name)
        )
    return name


@tier1
@run_only_on('sat')
@parametrize('name', **valid_domain_names(length=5))
def test_positive_create_with_name(session, name):
    """Create a new domain with different names

    :id: 142f90e3-a2a3-4f99-8f9b-11189f230bc5

    :expectedresults: Domain is created

    :CaseImportance: Critical
    """
    with session:
        _create_domain(session, name)


@run_only_on('sat')
@tier1
@parametrize('name', **valid_domain_names(length=243))
def test_positive_create_with_long_name(session, name):
    """Create a new domain with long names

    :id: 0b856ad7-97a6-4632-8b84-1d8ee45bedc8

    :expectedresults: Domain is created

    :CaseImportance: Critical
    """
    with session:
        _create_domain(session, name)


@run_only_on('sat')
@upgrade
@tier1
def test_positive_delete(session):
    """Delete a domain

    :id: 07c1cc34-4569-4f04-9c4a-2842821a6977

    :expectedresults: Domain is deleted

    :CaseImportance: Critical
    """
    with session:
        name = _create_domain(session)
        session.domain.delete(name)
        assert not session.domain.search(name), (
            "Deleted domain '{}' still exists in UI"
            .format(name)
        )


@run_only_on('sat')
@tier1
@upgrade
@parametrize('new_name', **valid_domain_names(length=5))
def test_positive_update(session, new_name):
    """Update a domain with name and description

    :id: 25ff4a1d-3ca1-4153-be45-4fe1e63f3f16

    :expectedresults: Domain is updated

    :CaseImportance: Critical
    """
    with session:
        old_name = _create_domain(session)
        session.domain.update(old_name, {'domain.dns_domain': new_name})
        assert session.domain.search(new_name), (
            "Unable to find domain '{}' after changing name (old name: {})"
            .format(new_name, old_name)
        )


@run_only_on('sat')
@tier1
@parametrize('name', **invalid_domain_names())
def test_negative_create_with_invalid_name(session, name):
    """Try to create domain and use whitespace, blank, tab symbol or
    too long string of different types as its name value

    :id: 5a8ba1a8-2da8-48e1-8b2a-96d91161bf94

    :expectedresults: Domain is not created

    :CaseImportance: Critical
    """
    with session:
        with pytest.raises(AssertionError) as context:
            _create_domain(session, name=name, assert_created=False)
        assert 'errors present' in str(context.value)


@run_only_on('sat')
@tier2
def test_positive_set_parameter(session):
    """Set parameter name and value for domain

    :id: a05615de-c9e5-4784-995c-b2fe2a1dfd3e

    :expectedresults: Domain is updated

    :CaseLevel: Integration
    """
    update_values = {
        'parameters.params': [
            {
                'name': gen_string('alpha'),
                'value': gen_string('alpha')
            }
        ]
    }
    with session:
        domain_name = _create_domain(session)
        session.domain.update(domain_name, update_values)


@run_only_on('sat')
@tier2
def test_positive_set_parameter_long(session):
    """Set a parameter in a domain with 255 chars in name and value.

    :id: b346ae66-1720-46af-b0da-460c52ce9476

    :expectedresults: Domain parameter is created.

    :CaseLevel: Integration
    """
    update_values = {
        'parameters.params': [
            {
                'name': gen_string('alpha', 255),
                'value': gen_string('alpha', 255)
            }
        ]
    }
    with session:
        domain_name = _create_domain(session)
        session.domain.update(domain_name, update_values)


@run_only_on('sat')
@tier2
def test_positive_set_parameter_blank(session):
    """Set a parameter in a domain with blank value.

    :id: b5a67709-57ad-4043-8e72-190ec31b8217

    :expectedresults: Domain parameter is created with blank value.

    :CaseLevel: Integration
    """
    update_values = {
        'parameters.params': [
            {
                'name': gen_string('alpha'),
                'value': ''
            }
        ]
    }
    with session:
        domain_name = _create_domain(session)
        session.domain.update(domain_name, update_values)


@run_only_on('sat')
@tier2
def test_negative_set_parameter(session):
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
        domain_name = _create_domain(session)
        with pytest.raises(AssertionError) as context:
            session.domain.update(domain_name, update_values)
        assert 'Name is too long' in str(context.value)


@run_only_on('sat')
@tier2
def test_negative_set_parameter_same(session):
    """Again set the same parameter for domain with name and value.

    :id: 6266f12e-cf94-4564-ba26-b467ced2737f

    :expectedresults: Domain parameter with same values is not created.

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        domain_name = _create_domain(session)
        session.domain.add_parameter(domain_name, param_name, param_value)
        with pytest.raises(AssertionError) as context:
            session.domain.add_parameter(domain_name, param_name, param_value)
        assert 'Name has already been taken' in str(context.value)


@run_only_on('sat')
@tier2
def test_positive_remove_parameter(session):
    """Remove a selected domain parameter

    :id: 8f7f8501-cf39-418f-a412-1a4b53698bc3

    :expectedresults: Domain parameter is removed

    :CaseLevel: Integration
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')
    with session:
        domain_name = _create_domain(session)
        session.domain.add_parameter(
            domain_name, param_name, param_value)
        session.domain.remove_parameter(
            domain_name, param_name)
        params = session.domain.read(domain_name)['parameters']['params']
        assert param_name not in [param['name'] for param in params]
