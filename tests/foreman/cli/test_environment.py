"""Tests for Environment  CLI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from fauxfactory import gen_string

from robottelo.cleanup import environment_cleanup
from robottelo.cleanup import location_cleanup
from robottelo.cleanup import org_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized


def _org(request):
    org = make_org()

    @request.addfinalizer
    def _cleanup():
        if Org.exists(search=('id', org['id'])):
            org_cleanup(org['id'])

    return org


def _location(request):
    location = make_location()

    @request.addfinalizer
    def _cleanup():
        if Location.exists(search=('id', location['id'])):
            location_cleanup(location['id'])

    return location


def _environment(request, options={}):
    environment = make_environment(options)

    @request.addfinalizer
    def _cleanup():
        if Environment.exists(search=('name', environment['name'])):
            environment_cleanup(environment['id'])

    return environment


def _puppet_class(org):
    """Setup for puppet class related tests"""
    puppet_modules = [{'author': 'robottelo', 'name': 'generic_1'}]
    cv = publish_puppet_module(puppet_modules, CUSTOM_PUPPET_REPO, org['id'])
    env = Environment.list({'search': 'content_view="{}"'.format(cv['name'])})[0]
    puppet_class = Puppet.info({'name': puppet_modules[0]['name'], 'environment': env['name']})
    return puppet_class


@pytest.fixture
def _make_org(request):
    """Create a new organization."""
    yield _org(request)


@pytest.fixture
def _make_loc(request):
    """Create a new location."""
    yield _location(request)


class TestEnvironment:
    """Test class for Environment CLI"""

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_negative_list_with_parameters(self, request, _make_org, _make_loc):
        """Test Environment List filtering parameters validation.

        :id: 97872953-e1aa-44bd-9ce0-a04bccbc9e94

        :expectedresults: Server returns empty result as there is no
            environment associated with location

        :CaseLevel: Integration

        :BZ: 1337947
        """
        _environment(
            request, {'organization-ids': _make_org['id'], 'location-ids': _make_loc['id']}
        )
        # Filter by non-existing location and existing organization
        with pytest.raises(CLIReturnCodeError):
            Environment.list(
                {'organization-id': _make_org['id'], 'location-id': gen_string('numeric')}
            )
        # Filter by non-existing organization and existing location
        with pytest.raises(CLIReturnCodeError):
            Environment.list(
                {'organization-id': gen_string('numeric'), 'location-id': _make_loc['id']}
            )
        # Filter by another location
        loc_2 = _location(request)
        results = Environment.list({'organization': _make_org['name'], 'location': loc_2['name']})
        assert len(results) == 0

    @pytest.mark.tier1
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, request, name):
        """Don't create an Environment with invalid data.

        :id: 8a4141b0-3bb9-47e5-baca-f9f027086d4c

        :expectedresults: Environment is not created.

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            _environment(request, {'name': name})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_CRUD_with_attributes(self, request, _make_org, _make_loc):
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
        environment = _environment(
            request,
            {
                'location-ids': _make_loc['id'],
                'organization-ids': _make_org['id'],
                'name': env_name,
            },
        )
        assert _make_loc['name'] in environment['locations']
        assert _make_org['name'] in environment['organizations']
        assert env_name == environment['name']

        # List by name
        result = Environment.list({'search': f'name={env_name}'})
        assert len(result) == 1
        assert result[0]['name'] == env_name

        # List by org loc id
        results = Environment.list(
            {'organization-id': _make_org['id'], 'location-id': _make_loc['id']}
        )
        assert env_name in [res['name'] for res in results]

        # List by org loc name
        results = Environment.list(
            {'organization': _make_org['name'], 'location': _make_loc['name']}
        )
        assert env_name in [res['name'] for res in results]

        # Update org and loc
        org_2 = _org(request)
        loc_2 = _location(request)
        Environment.update(
            {
                'location-ids': loc_2['id'],
                'organization-ids': org_2['id'],
                'name': environment['name'],
            }
        )
        env_info = Environment.info({'name': environment['name']})
        assert loc_2['name'] in env_info['locations']
        assert _make_loc['name'] not in env_info['locations']
        assert org_2['name'] in env_info['organizations']
        assert _make_org['name'] not in env_info['organizations']
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
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    @pytest.mark.parametrize('entity_id', **parametrized(invalid_id_list()))
    def test_negative_delete_by_id(self, entity_id):
        """Create Environment then delete it by wrong ID

        :id: fe77920c-62fd-4e0e-b960-a940a1370d10

        :expectedresults: Environment is not deleted

        :CaseImportance: Medium
        """
        with pytest.raises(CLIReturnCodeError):
            Environment.delete({'id': entity_id})

    @pytest.mark.tier1
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, request, name):
        """Update the Environment with invalid values

        :id: adc5ad73-0547-40f9-b4d4-649780cfb87a

        :expectedresults: Environment is not updated

        """
        environment = _environment(request)
        with pytest.raises(CLIReturnCodeError):
            Environment.update({'id': environment['id'], 'new-name': name})
        result = Environment.info({'id': environment['id']})
        assert environment['name'] == result['name']

    @pytest.mark.tier1
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_sc_params(self, _make_org):
        """Check if environment sc-param subcommand works passing
        an environment id

        :id: 32de4f0e-7b52-411c-a111-9ed472c3fc34

        :expectedresults: The command runs without raising an error

        """
        # Override one of the sc-params from puppet class
        puppet_class = _puppet_class(_make_org)
        env = Environment.list({'search': f"name={puppet_class['environments'][0]}"})[0]
        sc_params_list = SmartClassParameter.list(
            {
                'environment': env['name'],
                'search': f"puppetclass={puppet_class['name']}",
            }
        )
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        env_scparams = Environment.sc_params({'environment-id': env['id']})
        assert scp_id in [scp['id'] for scp in env_scparams]
