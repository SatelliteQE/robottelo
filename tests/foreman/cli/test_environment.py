"""Test for Environment  CLI

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
from nailgun import entities

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.config import settings
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.test import CLITestCase


class EnvironmentTestCase(CLITestCase):
    """Test class for Environment CLI"""

    @classmethod
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def setUpClass(cls):
        super().setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location().create()
        cls.loc2 = entities.Location().create()

        # Setup for puppet class related tests
        puppet_modules = [{'author': 'robottelo', 'name': 'generic_1'}]
        cls.cv = publish_puppet_module(puppet_modules, CUSTOM_PUPPET_REPO, cls.org.id)
        cls.env = Environment.list({'search': 'content_view="{}"'.format(cls.cv['name'])})[0]
        cls.puppet_class = Puppet.info(
            {'name': puppet_modules[0]['name'], 'environment': cls.env['name']}
        )

    @pytest.mark.tier2
    def test_negative_list_with_parameters(self):
        """Test Environment List filtering parameters validation.

        :id: 97872953-e1aa-44bd-9ce0-a04bccbc9e94

        :expectedresults: Server returns empty result as there is no
            environment associated with location

        :CaseLevel: Integration

        :BZ: 1337947
        """
        make_environment({'organization-ids': self.org.id, 'location-ids': self.loc.id})
        # Filter by non-existing location and existing organization
        with self.assertRaises(CLIReturnCodeError):
            Environment.list(
                {'organization-id': self.org.id, 'location-id': gen_string('numeric')}
            )
        # Filter by non-existing organization and existing location
        with self.assertRaises(CLIReturnCodeError):
            Environment.list(
                {'organization-id': gen_string('numeric'), 'location-id': self.loc.id}
            )
        # Filter by another location
        results = Environment.list({'organization': self.org.name, 'location': self.loc2.name})
        self.assertEqual(len(results), 0)

    @pytest.mark.tier1
    def test_negative_create_with_name(self):
        """Don't create an Environment with invalid data.

        :id: 8a4141b0-3bb9-47e5-baca-f9f027086d4c

        :expectedresults: Environment is not created.

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.create({'name': name})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_CRUD_with_attributes(self):
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
            {'location-ids': self.loc.id, 'organization-ids': self.org.id, 'name': env_name}
        )
        self.assertIn(self.loc.name, environment['locations'])
        self.assertIn(self.org.name, environment['organizations'])
        self.assertEqual(env_name, environment['name'])

        # List by name
        result = Environment.list({'search': f'name={env_name}'})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], env_name)
        # List by org loc id
        results = Environment.list({'organization-id': self.org.id, 'location-id': self.loc.id})
        self.assertIn(env_name, [res['name'] for res in results])
        # List by org loc name
        results = Environment.list({'organization': self.org.name, 'location': self.loc.name})
        self.assertIn(env_name, [res['name'] for res in results])

        # Update org and loc
        new_org = entities.Organization().create()
        Environment.update(
            {
                'location-ids': self.loc2.id,
                'organization-ids': new_org.id,
                'name': environment['name'],
            }
        )
        env_info = Environment.info({'name': environment['name']})
        self.assertIn(self.loc2.name, env_info['locations'])
        self.assertNotIn(self.loc.name, env_info['locations'])
        self.assertIn(new_org.name, env_info['organizations'])
        self.assertNotIn(self.org.name, env_info['organizations'])
        # Update name
        new_env_name = gen_string('alpha')
        Environment.update({'id': environment['id'], 'new-name': new_env_name})
        env_info = Environment.info({'id': environment['id']})
        self.assertEqual(env_info['name'], new_env_name)

        # Delete
        Environment.delete({'id': environment['id']})
        with self.assertRaises(CLIReturnCodeError):
            Environment.info({'id': environment['id']})

    @pytest.mark.tier1
    def test_negative_delete_by_id(self):
        """Create Environment then delete it by wrong ID

        :id: fe77920c-62fd-4e0e-b960-a940a1370d10

        :expectedresults: Environment is not deleted

        :CaseImportance: Medium
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.delete({'id': entity_id})

    @pytest.mark.tier1
    def test_negative_update_name(self):
        """Update the Environment with invalid values

        :id: adc5ad73-0547-40f9-b4d4-649780cfb87a

        :expectedresults: Environment is not updated

        """
        environment = make_environment()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.update({'id': environment['id'], 'new-name': new_name})
                result = Environment.info({'id': environment['id']})
                self.assertEqual(environment['name'], result['name'])

    @pytest.mark.tier1
    def test_positive_sc_params(self):
        """Check if environment sc-param subcommand works passing
        an environment id

        :id: 32de4f0e-7b52-411c-a111-9ed472c3fc34

        :expectedresults: The command runs without raising an error

        """
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list(
            {
                'environment': self.env['name'],
                'search': 'puppetclass="{}"'.format(self.puppet_class['name']),
            }
        )
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        env_scparams = Environment.sc_params({'environment-id': self.env['id']})
        self.assertIn(scp_id, [scp['id'] for scp in env_scparams])
