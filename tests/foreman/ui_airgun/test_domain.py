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
from nailgun import entities
import pytest

from robottelo.datafactory import valid_domain_names
from robottelo.decorators import fixture, parametrize, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


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
    new_param = {'name': gen_string('alpha', 255), 'value': param_value}
    with session:
        name = valid_domain_name
        session.domain.create({
            'domain.dns_domain': name,
            'domain.full_name': name,
        })
        session.domain.update(name, {'parameters.params': [new_param]})
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


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc, valid_domain_name):
    """Perform end to end testing for domain component

    :id: ce90fd87-3e63-4298-a771-38f4aacce091

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    dns_domain_name = valid_domain_name
    full_domain_name = gen_string('alpha')
    new_name = gen_string('alpha')
    param = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    with session:
        session.domain.create({
            'domain.dns_domain': dns_domain_name,
            'domain.full_name': full_domain_name,
            'parameters.params': [param],
            'locations.multiselect.assigned': [module_loc.name],
            'organizations.multiselect.assigned': [module_org.name],
        })
        assert session.domain.search(full_domain_name)[0]['Description'] == full_domain_name
        domain_values = session.domain.read(full_domain_name)
        assert domain_values['domain']['dns_domain'] == dns_domain_name
        assert domain_values['domain']['full_name'] == full_domain_name
        assert domain_values['parameters']['params'] == [param]
        assert domain_values['locations']['multiselect']['assigned'][0] == module_loc.name
        assert domain_values['organizations']['multiselect']['assigned'][0] == module_org.name
        # Update domain with new name
        session.domain.update(full_domain_name, {'domain.full_name': new_name})
        assert session.domain.search(new_name)[0]['Description'] == new_name
        # Delete domain
        session.domain.delete(new_name)
        assert not session.domain.search(new_name)
