"""Test for Environment  CLI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized


@pytest.fixture(scope='module')
def module_locations(default_sat):
    return (default_sat.api.Location().create(), default_sat.api.Location().create())


@pytest.mark.tier2
def test_negative_list_with_parameters(module_org, module_locations):
    """Test Environment List filtering parameters validation.

    :id: 97872953-e1aa-44bd-9ce0-a04bccbc9e94

    :expectedresults: Server returns empty result as there is no
        environment associated with location

    :CaseLevel: Integration

    :BZ: 1337947
    """
    make_environment({'organization-ids': module_org.id, 'location-ids': module_locations[0].id})
    # Filter by non-existing location and existing organization
    with pytest.raises(CLIReturnCodeError):
        Environment.list({'organization-id': module_org.id, 'location-id': gen_string('numeric')})
    # Filter by non-existing organization and existing location
    with pytest.raises(CLIReturnCodeError):
        Environment.list(
            {'organization-id': gen_string('numeric'), 'location-id': module_locations[0].id}
        )
    # Filter by another location
    results = Environment.list(
        {'organization': module_org.name, 'location': module_locations[1].name}
    )
    assert len(results) == 0


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name):
    """Don't create an Environment with invalid data.

    :id: 8a4141b0-3bb9-47e5-baca-f9f027086d4c

    :parametrized: yes

    :expectedresults: Environment is not created.

    :CaseImportance: Critical
    """
    with pytest.raises(CLIReturnCodeError):
        Environment.create({'name': name})


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_CRUD_with_attributes(default_sat, module_org, module_locations):
    """Check if Environment with attributes can be created, updated and removed

    :id: d2187971-86b2-40c9-a93c-66f37691ae2b

    :BZ: 1337947

    :expectedresults:
        1. Environment is created and has parameters assigned
        2. Environment can be listed by parameters
        3. Environment can be updated
        4. Environment can be removed

    :CaseImportance: Critical
    """
    # Create with attributes
    env_name = gen_string('alpha')
    environment = make_environment(
        {
            'location-ids': module_locations[0].id,
            'organization-ids': module_org.id,
            'name': env_name,
        }
    )
    assert module_locations[0].name in environment['locations']
    assert module_org.name in environment['organizations']
    assert env_name == environment['name']

    # List by name
    result = Environment.list({'search': f'name={env_name}'})
    assert len(result) == 1
    assert result[0]['name'] == env_name
    # List by org loc id
    results = Environment.list(
        {'organization-id': module_org.id, 'location-id': module_locations[0].id}
    )
    assert env_name in [res['name'] for res in results]
    # List by org loc name
    results = Environment.list(
        {'organization': module_org.name, 'location': module_locations[0].name}
    )
    assert env_name in [res['name'] for res in results]

    # Update org and loc
    new_org = default_sat.api.Organization().create()
    Environment.update(
        {
            'location-ids': module_locations[1].id,
            'organization-ids': new_org.id,
            'name': environment['name'],
        }
    )
    env_info = Environment.info({'name': environment['name']})
    assert module_locations[1].name in env_info['locations']
    assert module_locations[0].name not in env_info['locations']
    assert new_org.name in env_info['organizations']
    assert module_org.name not in env_info['organizations']
    # Update name
    new_env_name = gen_string('alpha')
    Environment.update({'id': environment['id'], 'new-name': new_env_name})
    env_info = Environment.info({'id': environment['id']})
    assert env_info['name'] == new_env_name

    # Delete
    Environment.delete({'id': environment['id']})
    with pytest.raises(CLIReturnCodeError):
        Environment.info({'id': environment['id']})


@pytest.mark.tier1
@pytest.mark.parametrize('entity_id', **parametrized(invalid_id_list()))
def test_negative_delete_by_id(entity_id):
    """Create Environment then delete it by wrong ID

    :id: fe77920c-62fd-4e0e-b960-a940a1370d10

    :parametrized: yes

    :expectedresults: Environment is not deleted

    :CaseImportance: Medium
    """
    with pytest.raises(CLIReturnCodeError):
        Environment.delete({'id': entity_id})


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
def test_negative_update_name(new_name):
    """Update the Environment with invalid values

    :id: adc5ad73-0547-40f9-b4d4-649780cfb87a

    :parametrized: yes

    :expectedresults: Environment is not updated

    """
    environment = make_environment()
    with pytest.raises(CLIReturnCodeError):
        Environment.update({'id': environment['id'], 'new-name': new_name})
    result = Environment.info({'id': environment['id']})
    assert environment['name'] == result['name']


@pytest.mark.tier1
@pytest.mark.skipif(
    not settings.robottelo.repos_hosting_url,
    reason='Missing repos_hosting_url',
)
def test_positive_sc_params(module_import_puppet_module):
    """Check if environment sc-param subcommand works passing
    an environment id

    :id: 32de4f0e-7b52-411c-a111-9ed472c3fc34

    :expectedresults: The command runs without raising an error

    """
    # Override one of the sc-params from puppet class
    sc_params_list = SmartClassParameter.list(
        {
            'environment': module_import_puppet_module['env'],
            'search': f'puppetclass="{module_import_puppet_module["puppet_class"]}"',
        }
    )
    scp_id = choice(sc_params_list)['id']
    SmartClassParameter.update({'id': scp_id, 'override': 1})
    # Verify that affected sc-param is listed
    env_scparams = Environment.sc_params({'environment': module_import_puppet_module['env']})
    assert scp_id in [scp['id'] for scp in env_scparams]
