"""Test class for Domain  CLI

:Requirement: Domain

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.domain import Domain
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.utils.datafactory import filtered_datapoint
from robottelo.utils.datafactory import invalid_id_list
from robottelo.utils.datafactory import parametrized


@filtered_datapoint
def valid_create_params():
    """Returns a list of valid domain create parameters"""
    return [
        {
            'name': 'white spaces {}'.format(gen_string(str_type='utf8')),
            'description': gen_string(str_type='alpha'),
        },
        {'name': gen_string(str_type='utf8'), 'description': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='numeric'), 'description': gen_string(str_type='numeric')},
        {
            'name': gen_string(str_type='utf8', length=255),
            'description': gen_string(str_type='utf8', length=255),
        },
    ]


@filtered_datapoint
def invalid_create_params():
    """Returns a list of invalid domain create parameters"""
    params = [{'name': gen_string(str_type='utf8', length=256)}]
    return params


@filtered_datapoint
def valid_update_params():
    """Returns a list of valid domain update parameters"""
    return [
        {
            'name': 'white spaces {}'.format(gen_string(str_type='utf8')),
            'description': gen_string(str_type='alpha'),
        },
        {'name': gen_string(str_type='utf8'), 'description': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='numeric'), 'description': gen_string(str_type='numeric')},
        {
            'name': gen_string(str_type='utf8', length=255),
            'description': gen_string(str_type='utf8', length=255),
        },
    ]


@filtered_datapoint
def invalid_update_params():
    """Returns a list of invalid domain update parameters"""
    params = [{'name': ''}, {'name': gen_string(str_type='utf8', length=256)}]
    return params


@filtered_datapoint
def valid_set_params():
    """Returns a list of valid domain set parameters"""
    return [
        {'name': gen_string(str_type='utf8'), 'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255), 'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'), 'value': gen_string(str_type='utf8', length=255)},
        {'name': gen_string(str_type='utf8'), 'value': ''},
    ]


@filtered_datapoint
def invalid_set_params():
    """Returns a list of invalid domain set parameters"""
    return [
        {
            'name': 'white spaces {}'.format(gen_string(str_type='utf8')),
            'value': gen_string(str_type='utf8'),
        },
        {'name': '', 'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=256), 'value': gen_string(str_type='utf8')},
    ]


@filtered_datapoint
def valid_delete_params():
    """Returns a list of valid domain delete parameters"""
    return [
        {'name': gen_string(str_type='utf8'), 'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8', length=255), 'value': gen_string(str_type='utf8')},
        {'name': gen_string(str_type='utf8'), 'value': ''},
    ]


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_update_delete_domain():
    """Create domain, update and delete domain and set parameters

    :id: 018740bf-1551-4162-b88e-4d4905af097b

    :expectedresults: Domain successfully created, updated and deleted

    :CaseImportance: Critical
    """
    options = valid_create_params()[0]
    location = make_location()
    org = make_org()
    domain = make_domain(
        {
            'name': options['name'],
            'description': options['description'],
            'location-ids': location['id'],
            'organization-ids': org['id'],
        }
    )
    assert domain['name'] == options['name']
    assert domain['description'] == options['description']
    assert location['name'] in domain['locations']
    assert org['name'] in domain['organizations']

    # set parameter
    parameter_options = valid_set_params()[0]
    parameter_options['domain-id'] = domain['id']
    Domain.set_parameter(parameter_options)
    domain = Domain.info({'id': domain['id']})
    parameter = {
        # Satellite applies lower to parameter's name
        parameter_options['name'].lower(): parameter_options['value']
    }
    assert parameter == domain['parameters']

    # update domain
    options = valid_update_params()[0]
    Domain.update(dict(options, id=domain['id']))
    # check - domain updated
    domain = Domain.info({'id': domain['id']})
    for key, val in options.items():
        assert domain[key] == val

    # delete parameter
    Domain.delete_parameter({'name': parameter_options['name'], 'domain-id': domain['id']})
    # check - parameter not set
    domain = Domain.info({'name': domain['name']})
    assert len(domain['parameters']) == 0

    # delete domain
    Domain.delete({'id': domain['id']})
    with pytest.raises(CLIReturnCodeError):
        Domain.info({'id': domain['id']})


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_create_params()))
def test_negative_create(options):
    """Create domain with invalid values

    :id: 6d3aec19-75dc-41ca-89af-fef0ca37082d

    :parametrized: yes

    :expectedresults: Domain is not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError):
        make_domain(options)


@pytest.mark.tier2
def test_negative_create_with_invalid_dns_id():
    """Attempt to register a domain with invalid id

    :id: 4aa52167-368a-41ad-87b7-41d468ad41a8

    :expectedresults: Error is raised and user friendly message returned

    :BZ: 1398392

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError) as context:
        make_domain({'name': gen_string('alpha'), 'dns-id': -1})
    valid_messages = ['Invalid smart-proxy id', 'Invalid capsule id']
    exception_string = str(context.value)
    messages = [message for message in valid_messages if message in exception_string]
    assert len(messages) > 0


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_update_params()))
def test_negative_update(module_domain, options):
    """Update domain with invalid values

    :id: 9fc708dc-20f9-4d7c-af53-863826462981

    :parametrized: yes

    :expectedresults: Domain is not updated

    :CaseImportance: Medium
    """
    with pytest.raises(CLIReturnCodeError):
        Domain.update(dict(options, id=module_domain.id))
    # check - domain not updated
    result = Domain.info({'id': module_domain.id})
    for key in options.keys():
        assert result[key] == getattr(module_domain, key)


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_set_params()))
def test_negative_set_parameter(module_domain, options):
    """Domain set-parameter with invalid values

    :id: 991fb849-83be-48f4-a12b-81eabb2bd8d3

    :parametrized: yes

    :expectedresults: Domain parameter is not set

    :CaseImportance: Low
    """
    options['domain-id'] = module_domain.id
    # set parameter
    with pytest.raises(CLIReturnCodeError):
        Domain.set_parameter(options)
    # check - parameter not set
    domain = Domain.info({'id': module_domain.id})
    assert len(domain['parameters']) == 0


@pytest.mark.tier2
@pytest.mark.parametrize('entity_id', **parametrized(invalid_id_list()))
def test_negative_delete_by_id(entity_id):
    """Create Domain then delete it by wrong ID

    :id: 0e4ef107-f006-4433-abc3-f872613e0b91

    :parametrized: yes

    :expectedresults: Domain is not deleted

    :CaseImportance: Medium
    """
    with pytest.raises(CLIReturnCodeError):
        Domain.delete({'id': entity_id})
